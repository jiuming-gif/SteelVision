import logging  # 导入logging库，用于记录日志信息
import numpy as np  # 导入NumPy库，用于处理数组和数值计算
import torch  # 导入PyTorch库，用于构建和训练深度学习模型
from PIL import Image, ImageEnhance, ImageDraw, ImageChops  # 导入PIL库，用于图像处理
from functools import partial  # 导入partial，用于将部分参数绑定到函数
from itertools import repeat  # 导入repeat，用于在函数中重复参数
from multiprocessing import Pool  # 导入Pool，用于并行处理任务
from os import listdir  # 导入listdir，用于列出指定目录中的文件
from os.path import splitext, isfile, join  # 导入splitext、isfile、join，用于文件路径处理
from pathlib import Path  # 导入Path，用于处理文件和目录路径
from torch.utils.data import Dataset  # 导入Dataset类，用于创建自定义数据集
from tqdm import tqdm  # 导入tqdm，用于显示进度条
import random  # 导入random库，用于生成随机数
import torchvision.transforms.functional as TF  # 导入torchvision，用于图像变换

def load_image(filename):
    """
    加载图像文件，根据文件扩展名的不同使用不同的加载方式。
    """
    ext = splitext(filename)[1]  # 获取文件扩展名
    if ext == '.npy':  # 如果是NumPy数组文件
        return Image.fromarray(np.load(filename))  # 使用NumPy加载文件，并转换为PIL图像
    elif ext in ['.pt', '.pth']:  # 如果是PyTorch张量文件
        return Image.fromarray(torch.load(filename).numpy())  # 加载PyTorch张量并转换为NumPy数组，再转换为PIL图像
    else:  # 如果是常规图像文件
        return Image.open(filename)  # 使用PIL直接打开图像文件

def unique_mask_values(idx, mask_dir, mask_suffix):
    """
    获取一个掩码图像文件的唯一值。通过索引从目录中找到对应的掩码文件，并返回其唯一值列表。
    """
    mask_file = list(mask_dir.glob(idx + mask_suffix + '.*'))[0]  # 根据索引和后缀在掩码目录中找到对应的掩码文件
    mask = np.asarray(load_image(mask_file))  # 加载掩码图像并转换为NumPy数组
    if mask.ndim == 2:  # 如果掩码图像是二维的
        return np.unique(mask)  # 返回掩码图像中的唯一值
    elif mask.ndim == 3:  # 如果掩码图像是三维的
        mask = mask.reshape(-1, mask.shape[-1])  # 将掩码图像展平为二维
        return np.unique(mask, axis=0)  # 返回掩码图像中的唯一值，考虑颜色通道
    else:
        raise ValueError(f'Loaded masks should have 2 or 3 dimensions, found {mask.ndim}')  # 如果掩码图像的维度不为2或3，抛出异常

class BasicDataset(Dataset):
    """
    自定义数据集类，用于加载和预处理图像及其对应的掩码，并进行数据增强。
    """
    def __init__(self, images_dir: str, mask_dir: str, scale: float = 1.0, mask_suffix: str = ''):
        self.images_dir = Path(images_dir)  # 图像目录路径
        self.mask_dir = Path(mask_dir)  # 掩码目录路径
        assert 0 < scale <= 1, 'Scale must be between 0 and 1'  # 确保缩放比例在0到1之间
        self.scale = scale  # 图像和掩码的缩放比例（此参数在本例中不使用）
        self.mask_suffix = mask_suffix  # 掩码文件的后缀

        # 获取图像目录中所有文件的ID（文件名去掉扩展名），并过滤掉隐藏文件
        self.ids = [splitext(file)[0] for file in listdir(images_dir)
                    if isfile(join(images_dir, file)) and not file.startswith('.')]
        if not self.ids:  # 如果没有找到图像文件，抛出异常
            raise RuntimeError(f'No input file found in {images_dir}, make sure you put your images there')

        logging.info(f'Creating dataset with {len(self.ids)} examples')  # 记录数据集创建的日志
        logging.info('Scanning mask files to determine unique values')  # 记录正在扫描掩码文件的日志

        # 使用多进程池扫描所有掩码文件，获取它们的唯一值
        with Pool() as p:
            unique = list(tqdm(
                p.imap(partial(unique_mask_values, mask_dir=self.mask_dir, mask_suffix=self.mask_suffix), self.ids),
                total=len(self.ids)
            ))

        # 合并所有掩码的唯一值，去重并排序
        self.mask_values = list(sorted(np.unique(np.concatenate(unique), axis=0).tolist()))
        logging.info(f'Unique mask values: {self.mask_values}')  # 记录唯一掩码值的日志

    def __len__(self):
        """
        返回数据集的大小，即图像文件的数量。
        """
        return len(self.ids)

    @staticmethod
    def preprocess(mask_values, pil_img, is_mask):
        """
        预处理图像或掩码：将图像缩放到224x224，并转换为适合模型输入的格式。
        """
        # 将图像缩放到224x224
        pil_img = pil_img.resize((224, 224), resample=Image.NEAREST if is_mask else Image.BICUBIC)
        img = np.asarray(pil_img)  # 将PIL图像转换为NumPy数组

        if is_mask:  # 如果是掩码
            mask = np.zeros((224, 224), dtype=np.int64)  # 创建与图像大小相同的空掩码数组
            for i, v in enumerate(mask_values):  # 遍历掩码中的每个唯一值
                if img.ndim == 2:  # 如果掩码是二维的
                    mask[img == v] = i  # 将与当前值匹配的像素设置为相应的索引
                else:
                    mask[(img == v).all(-1)] = i  # 如果掩码是三维的，考虑颜色通道
            return mask  # 返回预处理后的掩码
        else:
            if img.ndim == 2:  # 如果图像是灰度图（二维）
                img = img[np.newaxis, ...]  # 将其转换为三维（添加一个通道维度）
            else:  # 如果图像是RGB图（或其他多通道图）
                img = img.transpose((2, 0, 1))  # 调整维度顺序，使得通道维在最前面

            if (img > 1).any():  # 如果图像像素值超过1，表明图像像素值在0到255之间
                img = img / 255.0  # 将图像像素值归一化到0到1之间

            return img  # 返回预处理后的图像

    def __getitem__(self, idx):
        """
        根据索引获取图像及其对应的掩码，进行预处理和数据增强并返回。
        """
        name = self.ids[idx]  # 获取图像文件的ID
        mask_file = list(self.mask_dir.glob(name + self.mask_suffix + '.*'))  # 根据ID和后缀查找掩码文件
        img_file = list(self.images_dir.glob(name + '.*'))  # 根据ID查找图像文件
    
        # 确保每个ID只对应一个图像文件和一个掩码文件
        assert len(img_file) == 1, f'Either no image or multiple images found for the ID {name}: {img_file}'
        assert len(mask_file) == 1, f'Either no mask or multiple masks found for the ID {name}: {mask_file}'
    
        mask = load_image(mask_file[0])  # 加载掩码图像
        img = load_image(img_file[0])  # 加载图像
    
        # 确保图像和掩码的尺寸相同
        assert img.size == mask.size, \
            f'Image and mask {name} should be the same size, but are {img.size} and {mask.size}'
    
        # --- 数据增强部分 ---
        # 随机调整亮度
        img, mask = self.random_brightness(img, mask)
        # 随机调整对比度
        img, mask = self.random_contrast(img, mask)
        # 随机翻转
        img, mask = self.random_flip(img, mask)
        # 随机平移
        img, mask = self.random_translation(img, mask)
        # 随机旋转
        img, mask = self.random_rotation(img, mask)
    
        # --- 数据预处理 ---
        img = self.preprocess(self.mask_values, img, is_mask=False)  # 预处理图像
        mask = self.preprocess(self.mask_values, mask, is_mask=True)  # 预处理掩码
    
        return {
            'image': torch.as_tensor(img.copy()).float().contiguous(),  # 将图像转换为PyTorch张量并返回
            'mask': torch.as_tensor(mask.copy()).long().contiguous()  # 将掩码转换为PyTorch张量并返回
        }

    def random_brightness(self, img, mask):
        """
        随机亮度调整。
        """
        enhancer = ImageEnhance.Brightness(img)
        img_enhanced = enhancer.enhance(random.uniform(0.5, 1.5))
        return img_enhanced, mask

    def random_contrast(self, img, mask):
        """
        随机对比度调整。
        """
        enhancer = ImageEnhance.Contrast(img)
        img_enhanced = enhancer.enhance(random.uniform(0.5, 1.5))
        return img_enhanced, mask

    def random_flip(self, img, mask):
        """
        随机水平或垂直翻转。
        """
        # 以80%的概率进行翻转
        if random.random() < 0.8:
            flip_type = random.choice(['horizontal', 'vertical'])  # 随机选择水平或垂直翻转
            if flip_type == 'horizontal':  # 执行水平翻转
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
                mask = mask.transpose(Image.FLIP_LEFT_RIGHT)
            elif flip_type == 'vertical':  # 执行垂直翻转
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
                mask = mask.transpose(Image.FLIP_TOP_BOTTOM)
        return img, mask


    def random_translation(self, img, mask):
        """
        随机平移。
        """
        if random.random() < 0.25:
            max_shift = 10  # 最大平移像素
            x_shift = random.randint(-max_shift, max_shift)
            y_shift = random.randint(-max_shift, max_shift)
            img = ImageChops.offset(img, x_shift, y_shift)
            mask = ImageChops.offset(mask, x_shift, y_shift)
        return img, mask

    def random_rotation(self, img, mask):
        """
        随机旋转90°或180°。
        """
        if random.random() < 0.8:
            angle = random.choice([90, 180])
            img = img.rotate(angle, expand=True)
            mask = mask.rotate(angle, expand=True)
        return img, mask

class CarvanaDataset(BasicDataset):
    """
    一个具体的自定义数据集类，继承自BasicDataset类，专门处理Carvana数据集。
    """
    def __init__(self, images_dir, mask_dir, scale=1):
        super().__init__(images_dir, mask_dir, scale)  # 初始化父类并指定掩码文件的后缀
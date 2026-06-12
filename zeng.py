import os
from PIL import Image
import torchvision.transforms as transforms
import random

# 设置原图和标签图的路径
img_dir = "C:/Users/compelling/Desktop/task/data/imgs"  # 原图路径
mask_dir = "C:/Users/compelling/Desktop/task/data/masks"  # 标签图路径

# 创建增强后的图像和标签的保存路径
augmented_img_dir = "C:/Users/compelling/Desktop/task/data/imgs_augmented"  # 增强后的原图保存路径
augmented_mask_dir = "C:/Users/compelling/Desktop/task/data/masks_augmented"  # 增强后的标签图保存路径

# 如果保存路径不存在，创建这些文件夹
os.makedirs(augmented_img_dir, exist_ok=True)
os.makedirs(augmented_mask_dir, exist_ok=True)

# 数据增强的变换操作
augmentation_transforms = transforms.Compose([
    transforms.RandomHorizontalFlip(),  # 随机水平翻转
    transforms.RandomVerticalFlip(),  # 随机垂直翻转
    transforms.RandomRotation(90),  # 随机旋转0到90度
])

# 获取原图和标签图的文件列表
img_files = os.listdir(img_dir)
mask_files = os.listdir(mask_dir)

# 确保图像文件与标签文件对应
assert len(img_files) == len(mask_files), "图像和标签数量不匹配"

# 从004391开始编号
start_index = 4391  # 设置起始编号为 4391，这样生成的文件名为 004391

# 增强图像的计数器
enhanced_count = 0  # 初始化计数器

# 对每一对图像和标签进行相同的增强
for img_file, mask_file in zip(img_files, mask_files):
    if enhanced_count >= 2000:  # 检查是否已经增强了2000张图像
        break  # 达到2000张后退出循环

    img_path = os.path.join(img_dir, img_file)
    mask_path = os.path.join(mask_dir, mask_file)

    # 打开图像和标签
    img = Image.open(img_path)
    mask = Image.open(mask_path)

    # 确保图像和标签的尺寸相同
    assert img.size == mask.size, f"图像和标签尺寸不匹配: {img_file}, {mask_file}"

    # 对图像和标签同时进行相同的增强
    seed = random.randint(0, 2**32)  # 设置一个随机种子，确保图像和标签的变换一致
    random.seed(seed)
    augmented_img = augmentation_transforms(img)

    random.seed(seed)
    augmented_mask = augmentation_transforms(mask)

    # 生成新的文件名，从004391开始排序
    new_filename = f"00{start_index:04d}.png"  # 生成带有前缀 00 的六位数文件名，例如 004391.png
    start_index += 1  # 递增索引

    # 保存增强后的图像和标签
    augmented_img.save(os.path.join(augmented_img_dir, new_filename))  # 保存增强后的图像
    augmented_mask.save(os.path.join(augmented_mask_dir, new_filename))  # 保存增强后的标签

    # 增加计数器
    enhanced_count += 1  # 每次增强后，计数器加1

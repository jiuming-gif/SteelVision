import numpy as np

class Evaluator(object):
    def __init__(self, num_class):
        self.num_class = num_class
        self.confusion_matrix = np.zeros((self.num_class,) * 2)

    def Pixel_Accuracy(self):
        """
        Pixel Accuracy (PA): 所有正确分类像素的比例
        """
        PA = np.diag(self.confusion_matrix).sum() / self.confusion_matrix.sum()
        return PA

    def Pixel_Accuracy_Class(self):
        """
        Per-Class Pixel Accuracy (PAC): 每类的像素准确率
        """
        PAC = np.diag(self.confusion_matrix) / self.confusion_matrix.sum(axis=1)
        PAC = np.nanmean(PAC)
        return PAC

    def Mean_Pixel_Accuracy(self):
        """
        Mean Pixel Accuracy (mPA): 每类像素准确率的平均值
        """
        class_accuracy = np.diag(self.confusion_matrix) / self.confusion_matrix.sum(axis=1)
        return np.nanmean(class_accuracy)

    def Precision(self):
        """
        Precision: 每类精确率的平均值
        """
        with np.errstate(divide='ignore', invalid='ignore'):  # 忽略除零和无效计算的警告
            precision = np.diag(self.confusion_matrix) / self.confusion_matrix.sum(axis=0)
        
        # 将 NaN（无效值）替换为 0
        precision = np.nan_to_num(precision, nan=0.0)
        
        # 计算平均 Precision
        return np.mean(precision)


    def Recall(self):
        """
        Recall: 每类召回率的平均值
        """
        with np.errstate(divide='ignore', invalid='ignore'):  # 忽略除零和无效计算的警告
            recall = np.diag(self.confusion_matrix) / self.confusion_matrix.sum(axis=1)
        recall = np.nan_to_num(recall, nan=0.0)  # 将 NaN 替换为 0
        return np.mean(recall)

    def Mean_Intersection_over_Union(self, exclude_background=True, num_classes=4):
        """
        Mean IoU (MIoU): 每类 IoU 的平均值
        """
        with np.errstate(divide='ignore', invalid='ignore'):  # 忽略除零和无效计算的警告
            IoU_per_class = np.diag(self.confusion_matrix) / (
                np.sum(self.confusion_matrix, axis=1) +
                np.sum(self.confusion_matrix, axis=0) -
                np.diag(self.confusion_matrix)
            )
        
        # 将 NaN 替换为 0，确保计算结果有效
        IoU_per_class = np.nan_to_num(IoU_per_class, nan=0.0)
    
        if exclude_background:
            # 排除背景类别（通常为第 0 类）
            IoU_per_class_no_bg = IoU_per_class[1:num_classes]
            defect_mIoU = np.mean(IoU_per_class_no_bg)  # 计算非背景类别的平均 IoU
        else:
            IoU_per_class_no_bg = IoU_per_class
            defect_mIoU = np.mean(IoU_per_class)  # 包含背景类别的平均 IoU
    
        return IoU_per_class_no_bg, defect_mIoU


    def Frequency_Weighted_Intersection_over_Union(self):
        """
        Frequency Weighted IoU (FWIoU): 加权平均 IoU
        """
        freq = np.sum(self.confusion_matrix, axis=1) / np.sum(self.confusion_matrix)
        iu = np.diag(self.confusion_matrix) / (
            np.sum(self.confusion_matrix, axis=1) +
            np.sum(self.confusion_matrix, axis=0) -
            np.diag(self.confusion_matrix)
        )

        FWIoU = (freq[freq > 0] * iu[freq > 0]).sum()
        return FWIoU

    def _generate_matrix(self, gt_image, pre_image):
        """
        生成混淆矩阵
        """
        mask = (gt_image >= 0) & (gt_image < self.num_class)
        label = self.num_class * gt_image[mask].astype('int') + pre_image[mask]
        count = np.bincount(label, minlength=self.num_class**2)
        confusion_matrix = count.reshape(self.num_class, self.num_class)
        return confusion_matrix

    def add_batch(self, gt_image, pre_image):
        """
        更新混淆矩阵
        """
        assert gt_image.shape == pre_image.shape
        self.confusion_matrix += self._generate_matrix(gt_image, pre_image)

    def reset(self):
        """
        重置混淆矩阵
        """
        self.confusion_matrix = np.zeros((self.num_class,) * 2)

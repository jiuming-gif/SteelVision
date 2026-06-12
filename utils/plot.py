# -*- coding: UTF-8 -*-
import matplotlib.pyplot as plt
import os
from sklearn.metrics import confusion_matrix
import numpy as np
import seaborn as sns

def plot_miou(train_logs, val_logs, save_path):
    """
    绘制训练集和验证集的 mIoU 曲线
    """
    os.makedirs(save_path, exist_ok=True)

    plt.figure(figsize=(10, 6))

    x = list(range(1, len(train_logs) + 1))

    # 绘制训练集 mIoU 曲线（红色）
    plt.plot(x, train_logs, label='train', color='red', linewidth=2, linestyle='-', marker='o', markersize=5)

    # 绘制验证集 mIoU 曲线（蓝色）
    plt.plot(x, val_logs, label='valid', color='blue', linewidth=2, linestyle='--', marker='s', markersize=5)

    # 添加标题和标签
    plt.title('mIoU', fontsize=16)
    plt.xlabel('Epoch', fontsize=14)
    plt.ylabel('mIoU', fontsize=14)

    # 添加网格
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    # 设置轴范围
    plt.xlim(min(x), max(x))

    # 添加图例
    plt.legend(loc='lower right', fontsize=12)

    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()

    # 保存图表
    plt.savefig(os.path.join(save_path, 'train_val_miou.png'), format='png')
    plt.close()


def plot_defect_iou(train_logs, val_logs, save_path):
    """
    绘制训练集和验证集三类缺陷的 IoU 曲线
    """
    # 确保保存路径有效
    try:
        os.makedirs(save_path, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {save_path}: {e}")
        return

    # 确保训练集和验证集的缺陷类别一致
    common_defects = set(train_logs.keys()).intersection(val_logs.keys())
    if not common_defects:
        print("No common defect names between train_logs and val_logs.")
        return

    for defect_name in common_defects:
        plt.figure(figsize=(10, 6))

        # 横轴：epoch
        x_train = list(range(1, len(train_logs[defect_name]) + 1))
        x_val = list(range(1, len(val_logs[defect_name]) + 1))

        # 绘制训练集 IoU 曲线（红色）
        plt.plot(
            x_train, train_logs[defect_name],
            label='train', color='red', linestyle='-', marker='o', markersize=5
        )

        # 绘制验证集 IoU 曲线（蓝色）
        plt.plot(
            x_val, val_logs[defect_name],
            label='valid', color='blue', linestyle='--', marker='s', markersize=5
        )

        # 添加标题和标签
        plt.title(f'{defect_name} IoU', fontsize=16)
        plt.xlabel('Epoch', fontsize=14)
        plt.ylabel('IoU', fontsize=14)

        # 添加网格
        plt.grid(True, linestyle='--', linewidth=0.5)

        # 设置轴范围
        plt.xlim(1, max(len(x_train), len(x_val)))
        plt.ylim(0, 1)

        # 添加图例
        plt.legend(loc='lower right', fontsize=12)

        # 调整字体大小
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)

        # 自动调整布局
        plt.tight_layout()

        # 保存图表
        try:
            file_path = os.path.join(save_path, f'{defect_name}_iou.png')
            plt.savefig(file_path, format='png')
            print(f"Saved plot to {file_path}")
        except Exception as e:
            print(f"Error saving plot for {defect_name}: {e}")

        plt.close()


def plot_loss(train_logs, val_logs, save_path):
    """
    绘制训练集和验证集的损失函数曲线
    """
    # 确保保存路径有效
    os.makedirs(save_path, exist_ok=True)

    # 创建绘图窗口
    plt.figure(figsize=(10, 6))

    # 横轴：epoch
    x = list(range(1, len(train_logs) + 1))

    # 绘制训练集损失曲线（红色）
    plt.plot(x, train_logs, label='train', color='red', linestyle='-', marker='o', markersize=5, linewidth=2)

    # 绘制验证集损失曲线（蓝色）
    plt.plot(x, val_logs, label='valid', color='blue', linestyle='--', marker='s', markersize=5, linewidth=2)

    # 添加标题和标签
    plt.title('Loss Curve', fontsize=16)
    plt.xlabel('Epoch', fontsize=14)
    plt.ylabel('Loss', fontsize=14)

    # 添加网格
    plt.grid(True, linestyle='--', linewidth=0.5)

    # 设置横轴范围
    plt.xlim(min(x), max(x))

    # 添加图例
    plt.legend(loc='upper right', fontsize=12)

    # 调整字体大小
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # 自动调整布局
    plt.tight_layout()

    # 保存图表
    file_path = os.path.join(save_path, 'train_val_loss.png')
    plt.savefig(file_path, format='png')
    plt.close()

    print(f"Saved loss curve to {file_path}")


def plot_recall(train_recall_logs, val_recall_logs, save_path):
    """
    绘制训练集和验证集的 Recall 曲线。
    """
    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)

    # 创建绘图窗口
    plt.figure(figsize=(10, 6))

    # 横轴：epoch
    x = list(range(1, len(train_recall_logs) + 1))

    # 绘制训练集 Recall 曲线（红色）
    plt.plot(x, train_recall_logs, label='train', color='red', linestyle='-', marker='o', markersize=5, linewidth=2)

    # 绘制验证集 Recall 曲线（蓝色）
    plt.plot(x, val_recall_logs, label='valid', color='blue', linestyle='--', marker='s', markersize=5, linewidth=2)

    # 添加标题和标签
    plt.title('Recall Curve', fontsize=16)
    plt.xlabel('Epoch', fontsize=14)
    plt.ylabel('Recall', fontsize=14)

    # 添加网格
    plt.grid(True, linestyle='--', linewidth=0.5)

    # 设置横轴范围
    plt.xlim(min(x), max(x))

    # 添加图例
    plt.legend(loc='lower right', fontsize=12)

    # 调整字体大小
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # 自动调整布局
    plt.tight_layout()

    # 保存图表
    file_path = os.path.join(save_path, 'train_val_recall.png')
    plt.savefig(file_path, format='png')
    plt.close()

    print(f"Saved recall curve to {file_path}")


def plot_precision(train_precision_logs, val_precision_logs, save_path):
    """
    绘制训练集和验证集的 Precision 曲线
    """
    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)

    # 创建绘图窗口
    plt.figure(figsize=(10, 6))

    # 横轴：epoch
    x = list(range(1, len(train_precision_logs) + 1))

    # 绘制训练集 Precision 曲线（红色）
    plt.plot(x, train_precision_logs, label='train', color='red', linestyle='-', marker='o', markersize=5, linewidth=2)

    # 绘制验证集 Precision 曲线（蓝色）
    plt.plot(x, val_precision_logs, label='valid', color='blue', linestyle='--', marker='s', markersize=5, linewidth=2)

    # 添加标题和标签
    plt.title('Precision Curve', fontsize=16)
    plt.xlabel('Epoch', fontsize=14)
    plt.ylabel('Precision', fontsize=14)

    # 添加网格
    plt.grid(True, linestyle='--', linewidth=0.5)

    # 设置横轴范围
    plt.xlim(min(x), max(x))

    # 添加图例
    plt.legend(loc='lower right', fontsize=12)

    # 调整字体大小
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # 自动调整布局
    plt.tight_layout()

    # 保存图表
    file_path = os.path.join(save_path, 'train_val_precision.png')
    plt.savefig(file_path, format='png')
    plt.close()

    print(f"Saved precision curve to {file_path}")


def plot_f1_score(train_f1_logs, val_f1_logs, save_path):
    """
    绘制训练集和验证集的 F1 Score 曲线

    Args:
        train_f1_logs (list): 每个 epoch 的训练集 F1 Score
        val_f1_logs (list): 每个 epoch 的验证集 F1 Score
        save_path (str): 保存绘图的路径
    """
    # 确保保存路径有效
    os.makedirs(save_path, exist_ok=True)

    # 创建绘图窗口
    plt.figure(figsize=(10, 6))

    # 横轴：epoch
    x = list(range(1, len(train_f1_logs) + 1))

    # 绘制训练集 F1 Score 曲线（红色）
    plt.plot(x, train_f1_logs, label='train', color='red', linestyle='-', marker='o', markersize=5, linewidth=2)

    # 绘制验证集 F1 Score 曲线（蓝色）
    plt.plot(x, val_f1_logs, label='valid', color='blue', linestyle='--', marker='s', markersize=5, linewidth=2)

    # 添加标题和标签
    plt.title('F1 Score Curve', fontsize=16)
    plt.xlabel('Epoch', fontsize=14)
    plt.ylabel('F1 Score', fontsize=14)

    # 添加网格
    plt.grid(True, linestyle='--', linewidth=0.5)

    # 设置横轴范围
    plt.xlim(min(x), max(x))
    plt.ylim(0, 1)  # F1 Score 的范围是 0 到 1

    # 添加图例
    plt.legend(loc='lower right', fontsize=12)

    # 调整字体大小
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # 自动调整布局
    plt.tight_layout()

    # 保存图表
    file_path = os.path.join(save_path, 'train_val_f1_score.png')
    plt.savefig(file_path, format='png')
    plt.close()

    print(f"Saved F1 Score curve to {file_path}")

def plot_confusion_matrix(cm, class_names, save_path=None, normalize=True, title="Confusion Matrix"):
    """
    绘制混淆矩阵

    Args:
        cm (np.ndarray): 混淆矩阵，大小为 (num_classes, num_classes)
        class_names (list): 类别名称列表
        save_path (str): 保存路径，如果为 None，则直接显示
        normalize (bool): 是否将混淆矩阵归一化
        title (str): 图表标题
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np

    # 归一化混淆矩阵
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1, keepdims=True)
        cm = np.nan_to_num(cm)  # 防止分母为 0 导致 NaN

    # 创建图表
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt=".2f" if normalize else "d", cmap="Blues", xticklabels=class_names, yticklabels=class_names, cbar=False)

    # 设置标题和轴标签
    plt.title(title, fontsize=16)
    plt.xlabel('Predicted Class', fontsize=14)
    plt.ylabel('True Class', fontsize=14)

    # 设置坐标轴刻度字体水平显示
    plt.xticks(rotation=0, fontsize=12, ha='center')  # 设置 x 轴文字水平显示并居中
    plt.yticks(rotation=0, fontsize=12, va='center')  # 设置 y 轴文字水平显示并居中

    # 自动调整布局
    plt.tight_layout()

    # 保存或展示图表
    if save_path:
        plt.savefig(save_path, format='png', bbox_inches='tight')
        print(f"Confusion matrix saved to {save_path}")
    else:
        plt.show()

    plt.close()

    
def compute_confusion_matrix(true_labels, pred_labels, num_classes):
    """
    计算混淆矩阵

    Args:
        true_labels (np.ndarray): 真实标签，形状为 (H, W)
        pred_labels (np.ndarray): 预测标签，形状为 (H, W)
        num_classes (int): 类别总数

    Returns:
        cm (np.ndarray): 混淆矩阵
    """
    # 将二维标签展平为一维
    true_labels = true_labels.flatten()
    pred_labels = pred_labels.flatten()

    # 计算混淆矩阵
    cm = confusion_matrix(true_labels, pred_labels, labels=np.arange(num_classes))

    return cm

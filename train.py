import argparse
import logging
import os
import random
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
import torchvision.transforms.functional as TF
from pathlib import Path
from torch import optim
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm
import numpy as np
import wandb
import evaluate
from model.model import self_net
from utils.data_loading import BasicDataset, CarvanaDataset
from utils.dice_score import dice_loss
from utils.metrics import Evaluator
from torch.cuda.amp import autocast
from utils.plot import plot_miou, plot_defect_iou, plot_loss, plot_recall, plot_precision, plot_f1_score, plot_confusion_matrix, compute_confusion_matrix

# 设置路径，定义图像、掩码和检查点的目录
dir_img = Path('/root/task/data/train/imgs')
dir_mask = Path('/root/task/data/train/masks')
valid_img = Path('/root/task/data/valid/imgs')
valid_mask = Path('/root/task/data/valid/masks')
save_plot_path = Path('/root/task/plots')  # 保存曲线图的目录

def validate_model(model, val_loader, evaluator, device, epoch, criterion, amp=True):
    """
    验证模型，返回每类 IoU、去除背景后的平均 mIoU，以及验证集的平均损失、Recall 和 Precision。
    同时计算并绘制混淆矩阵和 F1 Score。
    """
    model.eval()
    evaluator.reset()
    epoch_val_loss = 0  # 当前 epoch 的验证损失

    # 保存验证集所有批次的真实标签和预测标签
    true_labels_all = []
    pred_labels_all = []

    with tqdm(total=len(val_loader), desc=f'Validation Epoch {epoch}', unit='batch') as pbar:
        with torch.no_grad():
            for batch in val_loader:
                images, true_masks = batch['image'], batch['mask']
                images = images.to(device=device, dtype=torch.float32)
                true_masks = true_masks.to(device=device, dtype=torch.long)

                with autocast(enabled=amp):
                    masks_pred = model(images)
                    val_loss = criterion(masks_pred, true_masks) + dice_loss(
                        F.softmax(masks_pred, dim=1).float(),
                        F.one_hot(true_masks, model.n_classes).permute(0, 3, 1, 2).float(),
                        multiclass=True
                    )
                    epoch_val_loss += val_loss.item()

                # 获取预测和真实标签
                pred_masks = masks_pred.argmax(dim=1).cpu().numpy()
                true_masks = true_masks.cpu().numpy()

                # 收集所有真实标签和预测标签
                true_labels_all.append(true_masks)
                pred_labels_all.append(pred_masks)

                # 添加到 evaluator
                evaluator.add_batch(true_masks, pred_masks)
                IoU_per_class_no_bg, defect_mIoU = evaluator.Mean_Intersection_over_Union()
                recall = evaluator.Recall()  # 计算 Recall
                precision = evaluator.Precision()  # 计算 Precision
                pbar.set_postfix({'Validation mIoU (batch)': defect_mIoU, 'Recall (batch)': recall, 'Precision (batch)': precision})
                pbar.update(1)

    # 计算验证集的平均损失
    avg_val_loss = epoch_val_loss / len(val_loader)

    # 计算验证集整体的 IoU、Recall 和 Precision
    IoU_per_class_no_bg, defect_mIoU = evaluator.Mean_Intersection_over_Union()
    recall = evaluator.Recall()
    precision = evaluator.Precision()

    # 计算 F1 Score
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    print(f'Epoch {epoch} - Validation F1 Score: {f1_score:.4f}')

    return IoU_per_class_no_bg, defect_mIoU, avg_val_loss, recall, precision

def train_model(
    model,
    device,
    epochs: int = 100,
    batch_size: int = 8,
    learning_rate: float = 1e-6,
    val_percent: float = 0.1,
    save_checkpoint: bool = True,
    img_scale: float = 0.5,
    amp: bool = False,
    weight_decay: float = 1e-8,
    momentum: float = 0.999,
    gradient_clipping: float = 1.0,
):
    # 初始化训练和验证的 mIoU 记录
    train_miou_logs = []
    val_miou_logs = []
    # 定义用于存储训练和验证损失的列表
    train_loss_logs = []
    val_loss_logs = []
    # 初始化训练和验证的 Recall 记录
    train_recall_logs = []
    val_recall_logs = []
    # 初始化训练和验证的 Precision 记录
    train_precision_logs = []
    val_precision_logs = []

    # 1. 创建训练集
    try:
        dataset = CarvanaDataset(dir_img, dir_mask, img_scale)
    except (AssertionError, RuntimeError, IndexError):
        dataset = BasicDataset(dir_img, dir_mask, img_scale)

    # 2. 创建训练集数据加载器
    loader_args = dict(batch_size=batch_size, num_workers=2, pin_memory=True)
    train_loader = DataLoader(dataset, shuffle=True, **loader_args)

    # 3. 加载自定义验证集
    try:
        val_dataset = CarvanaDataset(valid_img, valid_mask, img_scale)
    except (AssertionError, RuntimeError, IndexError):
        val_dataset = BasicDataset(valid_img, valid_mask, img_scale)

    # 创建验证集数据加载器
    val_loader = DataLoader(val_dataset, shuffle=False, drop_last=True, **loader_args)
    logging.info(f'''Starting training:
        Epochs: {epochs}
        Batch size: {batch_size}
        Learning rate: {learning_rate}
        Training size: {len(dataset)}
        Validation size: {len(val_dataset)}
        Checkpoints: {save_checkpoint}
        Device: {device.type}
        Images scaling: {img_scale}
        Mixed Precision: {amp}
    ''')

    # 4. 设置优化器、损失函数和学习率调度器
    optimizer = optim.RMSprop(model.parameters(),
                              lr=learning_rate, weight_decay=weight_decay, momentum=momentum, foreach=True)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'max', patience=5)
    grad_scaler = torch.cuda.amp.GradScaler(enabled=amp)
    criterion = nn.CrossEntropyLoss()
    global_step = 0

    # 初始化记录最好的 mIoU 和最小的验证集损失
    best_miou = -float('inf')
    best_loss = float('inf')  # 初始化为正无穷大

    # 5. 开始训练
    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0
        evaluator = Evaluator(num_class=model.n_classes)  # 每轮重新初始化 Evaluator

        with tqdm(total=len(train_loader.dataset), desc=f'Epoch {epoch}/{epochs}', unit='img') as pbar:
            for batch in train_loader:
                images, true_masks = batch['image'], batch['mask']
            
                images = images.to(device=device, dtype=torch.float32, memory_format=torch.channels_last)
                true_masks = true_masks.to(device=device, dtype=torch.long)
            
                with torch.autocast(device.type if device.type != 'mps' else 'cpu', enabled=amp):
                    masks_pred = model(images)
                    loss = criterion(masks_pred, true_masks)
                    loss += dice_loss(
                        F.softmax(masks_pred, dim=1).float(),
                        F.one_hot(true_masks, model.n_classes).permute(0, 3, 1, 2).float(),
                        multiclass=True
                    )
            
                optimizer.zero_grad(set_to_none=True)
                grad_scaler.scale(loss).backward()
                grad_scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clipping)
                grad_scaler.step(optimizer)
                grad_scaler.update()
            
                pbar.update(images.shape[0])
                global_step += 1
                epoch_loss += loss.item()

                # 计算训练集的 mIoU、Recall 和 Precision
                pred_masks = masks_pred.argmax(dim=1).cpu().numpy()
                true_masks = true_masks.cpu().numpy()
                evaluator.add_batch(true_masks, pred_masks)  # 更新混淆矩阵
                
                # 记录训练损失、mIoU、Recall 和 Precision
                IoU_per_class_no_bg, defect_mIoU = evaluator.Mean_Intersection_over_Union()
                recall = evaluator.Recall()  # 计算 Recall
                precision = evaluator.Precision()  # 计算 Precision
                pbar.set_postfix(mIoU=defect_mIoU, Recall=recall, Precision=precision)
            
            # 每个 epoch 结束时，计算并记录训练集的 mIoU、Recall 和 Precision
            IoU_per_class_no_bg, defect_mIoU = evaluator.Mean_Intersection_over_Union()
            recall = evaluator.Recall()
            precision = evaluator.Precision()
            train_miou_logs.append(defect_mIoU)
            train_recall_logs.append(recall)
            train_precision_logs.append(precision)

            # 记录训练损失
            avg_train_loss = epoch_loss / len(train_loader)
            train_loss_logs.append(avg_train_loss)
                
            print(f'Epoch {epoch}, Training IoU: {IoU_per_class_no_bg}, mIoU: {defect_mIoU}, Recall: {recall}, Precision: {precision}, Loss/train: {avg_train_loss}')

        # 验证阶段：计算验证集的 mIoU、Recall、Precision 和损失
        val_IoU_per_class_no_bg, avg_val_miou, avg_val_loss, val_recall, val_precision = validate_model(
            model, val_loader, evaluator, device, epoch, criterion, amp=amp
        )

        val_miou_logs.append(avg_val_miou)
        val_recall_logs.append(val_recall)
        val_precision_logs.append(val_precision)
        val_loss_logs.append(avg_val_loss)

        # 保存最佳模型（基于 mIoU 和验证损失）
        if avg_val_miou > best_miou:
            best_miou = avg_val_miou
            if save_checkpoint:
                torch.save(model.state_dict(), '/root/task/best_model/best_model_miou_impro_1.pth')
            
        if avg_val_loss < best_loss:
            best_loss = avg_val_loss
            if save_checkpoint:
                torch.save(model.state_dict(), '/root/task/best_model/best_model_loss_impro_1.pth')
            
        # 绘制曲线
        plot_miou(train_miou_logs, val_miou_logs, save_plot_path)
        plot_recall(train_recall_logs, val_recall_logs, save_plot_path)
        plot_precision(train_precision_logs, val_precision_logs, save_plot_path)
        plot_loss(train_loss_logs, val_loss_logs, save_plot_path)

        # 绘制 F1 Score 曲线
        train_f1_scores = [2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0 for prec, rec in zip(train_precision_logs, train_recall_logs)]
        val_f1_scores = [2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0 for prec, rec in zip(val_precision_logs, val_recall_logs)]
        plot_f1_score(train_f1_scores, val_f1_scores, save_plot_path)

        # 计算并绘制混淆矩阵
        true_labels_all = []
        pred_labels_all = []

        for batch in val_loader:
            images, true_masks = batch['image'], batch['mask']
            images = images.to(device=device, dtype=torch.float32)
            true_masks = true_masks.to(device=device, dtype=torch.long)

            with torch.no_grad():
                masks_pred = model(images).argmax(dim=1).cpu().numpy()
                true_masks = true_masks.cpu().numpy()

            true_labels_all.append(true_masks)
            pred_labels_all.append(masks_pred)

        true_labels_all = np.concatenate([m.flatten() for m in true_labels_all])
        pred_labels_all = np.concatenate([m.flatten() for m in pred_labels_all])

        cm = compute_confusion_matrix(true_labels_all, pred_labels_all, model.n_classes)
        class_names = ['Background', 'Inclusions', 'Patches', 'Scratches']
        plot_confusion_matrix(cm, class_names, save_path=os.path.join(save_plot_path, 'confusion_matrix.png'))

    print('训练完成。')

def get_args():
    parser = argparse.ArgumentParser(description='Train the UNet on images and target masks')
    parser.add_argument('--epochs', '-e', metavar='E', type=int, default=120, help='Number of epochs')
    parser.add_argument('--batch-size', '-b', dest='batch_size', metavar='B', type=int, default=16, help='Batch size')
    parser.add_argument('--learning-rate', '-l', metavar='LR', type=float, default=1e-6,
                        help='Learning rate', dest='lr')
    parser.add_argument('--load', '-f', type=str, default=False, help='Load model from a .pth file')
    parser.add_argument('--scale', '-s', type=float, default=0.5, help='Downscaling factor of the images')
    parser.add_argument('--validation', '-v', dest='val', type=float, default=10.0,
                        help='Percent of the data that is used as validation (0-100)')
    parser.add_argument('--amp', action='store_true', default=False, help='Use mixed precision')
    parser.add_argument('--bilinear', action='store_true', default=False, help='Use bilinear upsampling')
    parser.add_argument('--classes', '-c', type=int, default=4, help='Number of classes')

    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f'Using device {device}')

    # 初始化模型
    model = self_net(n_channels=3, n_classes=4, bilinear=True)
    model = model.to(memory_format=torch.channels_last)

    logging.info(f'Network:\n'
                 f'\t{model.n_channels} input channels\n'
                 f'\t{model.n_classes} output channels (classes)\n'
                 f'\t{"Bilinear" if model.bilinear else "Transposed conv"} upscaling')

    if args.load:
        # 如果需要加载模型
        model.load_state_dict(torch.load(args.load, map_location=device))
        logging.info(f'Model loaded from {args.load}')

    model.to(device=device)
    try:
        train_model(
            model=model,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr,
            device=device,
            img_scale=args.scale,
            val_percent=args.val / 100,
            amp=args.amp
        )
    except RuntimeError as e:
        if 'out of memory' in str(e):
            logging.error('Detected OutOfMemoryError! Enabling checkpointing to reduce memory usage.')
            torch.cuda.empty_cache()

            # 手动启用梯度检查点功能
            train_model(
                model=model,
                epochs=args.epochs,
                batch_size=args.batch_size,
                learning_rate=args.lr,
                device=device,
                img_scale=args.scale,
                val_percent=args.val / 100,
                amp=args.amp
            )
        else:
            raise e

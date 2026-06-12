
import os
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from io import BytesIO
import time
from typing import Tuple, Dict, Any, List

# 假设您已有以下模块：
from utils.data_loading import BasicDataset
from model.model import self_net

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# 确保这里的路径是正确的，指向您的模型文件
model_path = "./best_model/best_model_miou.pth"

def load_cv_model():
    """加载CV模型"""
    net = self_net()
    # 检查模型文件是否存在
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件未找到: {model_path}")
    state_dict = torch.load(model_path, map_location=device)
    net.load_state_dict(state_dict)
    net.to(device)
    net.eval()
    return net

# 在模块加载时加载模型，确保只加载一次
try:
    cv_model = load_cv_model()
    print(f"CV模型 {model_path} 加载成功，运行在 {device} 上。")
except FileNotFoundError as e:
    print(f"错误: {e}. 请确保模型文件存在。")
    cv_model = None # If model not found, set to None

async def perform_detection(image_bytes: bytes) -> Tuple[List[List[int]], float]:
    """
    执行图像缺陷检测。
    Args:
        image_bytes: 图像的字节数据。
    Returns:
        Tuple[List[List[int]], float]: 像素级缺陷掩码 (mask) 及其模型推理时间 (ms)。
    """
    if cv_model is None:
        raise RuntimeError("CV模型未加载，无法执行检测。")

    pil_img = Image.open(BytesIO(image_bytes)).convert("RGB")
    orig_w, orig_h = pil_img.size

    # preprocess 内部会缩放到 224x224 并归一化
    img_tensor = torch.from_numpy(BasicDataset.preprocess(None, pil_img, is_mask=False))
    img_tensor = img_tensor.unsqueeze(0).to(device=device, dtype=torch.float32)

    start_infer = time.time()
    with torch.no_grad():
        output = cv_model(img_tensor).cpu()  # shape: (1, n_classes, 224, 224)
    end_infer = time.time()
    model_inference_ms = (end_infer - start_infer) * 1000

    # 插值回原图大小
    output = F.interpolate(output, (orig_h, orig_w), mode='bilinear')
    mask = output.argmax(dim=1).squeeze().numpy().astype(np.uint8)

    return mask.tolist(), model_inference_ms

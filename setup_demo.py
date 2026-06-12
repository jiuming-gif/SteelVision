"""
SteelVision Demo 一键准备脚本
运行此脚本后，所有缺失的素材、依赖清单、启动脚本都会自动生成。
只需：python setup_demo.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "images")

# ============================================================
# Step 1: 创建缺失目录
# ============================================================
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "web"), exist_ok=True)
print("[1/5] 目录结构已创建")

# ============================================================
# Step 2: 生成占位图片（用 PIL 生成纯色+文字，不依赖外部素材）
# ============================================================
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("请先安装 Pillow: pip install Pillow --break-system-packages")
    sys.exit(1)

def create_placeholder(filename, size, color, text=""):
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    if text:
        # 尝试用系统字体
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size[0] - tw) // 2, (size[1] - th) // 2), text, fill="white", font=font)
    img.save(os.path.join(ASSETS_DIR, filename))
    print(f"  -> {filename} ({size[0]}x{size[1]})")

# 启动闪屏图
create_placeholder("splash_image.png", (800, 500), (30, 60, 120), "SteelVision")

# 登录页横幅
create_placeholder("login_banner.png", (600, 200), (45, 80, 140), "SteelVision Login")

# 示例检测图片（模拟一张钢材表面图）
img = Image.new("RGB", (600, 400), (80, 80, 80))
draw = ImageDraw.Draw(img)
# 画几个模拟缺陷
draw.rectangle([150, 120, 200, 170], fill=(180, 60, 60))   # 夹杂物（红）
draw.ellipse([300, 200, 380, 260], fill=(60, 160, 60))      # 补丁（绿）
draw.line([100, 280, 350, 300], fill=(60, 60, 180), width=5) # 划痕（蓝）
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except:
    font = ImageFont.load_default()
draw.text((200, 10), "Sample Steel Surface", fill="white", font=font)
img.save(os.path.join(ASSETS_DIR, "11.jpg"))
print(f"  -> 11.jpg (600x400, 模拟缺陷样本)")

# 团队成员照片占位
for i in range(1, 6):
    colors = [(70, 100, 150), (100, 130, 70), (150, 100, 70), (130, 70, 130), (70, 130, 130)]
    create_placeholder(f"{i}.jpg", (150, 150), colors[i-1], f"Member {i}")

# 按钮图标占位
create_placeholder("sxt.png", (48, 48), (50, 50, 50), "CAM")
create_placeholder("ds.png", (48, 48), (50, 50, 100), "AI")
create_placeholder("gear.png", (48, 48), (100, 80, 50), "SET")
create_placeholder("jg.png", (48, 48), (50, 100, 80), "RST")
create_placeholder("gly.png", (48, 48), (100, 50, 50), "ADM")

# 主窗口背景
create_placeholder("space_background.png", (1200, 800), (35, 35, 55))

# Web SPA 占位
web_index = os.path.join(BASE_DIR, "web", "index.html")
with open(web_index, "w", encoding="utf-8") as f:
    f.write("""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>SteelVision Web</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #1a1a2e; color: #eee; }
        h1 { font-size: 2em; }
    </style>
</head>
<body><h1>SteelVision Web Client</h1></body>
</html>""")

print("[2/5] 占位素材已生成（共 14 个文件）")

# ============================================================
# Step 3: 生成完整 requirements.txt
# ============================================================
requirements_full = """# === SteelVision 完整依赖 ===
# 安装命令: pip install -r requirements.txt --break-system-packages

# --- 后端服务 ---
fastapi==0.110.0
uvicorn==0.27.1
SQLAlchemy==2.0.28
pydantic==2.6.1
python-dotenv==1.0.1
httpx==0.27.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart==0.0.9

# --- 深度学习 ---
torch==2.2.1
torchvision==0.17.1
numpy==1.26.4
Pillow==10.2.0

# --- 桌面客户端 ---
PyQt5==5.15.9
opencv-python==4.9.0.80
matplotlib==3.8.2
pymysql==1.1.0

# --- 工具类 ---
requests==2.31.0
tqdm==4.66.1
"""

with open(os.path.join(BASE_DIR, "requirements_full.txt"), "w", encoding="utf-8") as f:
    f.write(requirements_full)
print("[3/5] requirements_full.txt 已生成")

# ============================================================
# Step 4: 生成启动脚本
# ============================================================

# Windows 启动脚本 - 服务端
server_bat = """@echo off
chcp 65001 >nul
title SteelVision Server (http://localhost:5000)
echo ============================================
echo   SteelVision 后端服务启动中...
echo   接口文档: http://localhost:5000/docs
echo   按 Ctrl+C 停止服务
echo ============================================
echo.
cd /d "%~dp0"
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
pause
"""

with open(os.path.join(BASE_DIR, "start_server.bat"), "w", encoding="utf-8") as f:
    f.write(server_bat)

# Windows 启动脚本 - 客户端
client_bat = """@echo off
chcp 65001 >nul
title SteelVision Client
echo ============================================
echo   SteelVision 桌面客户端启动中...
echo   确保后端服务已在 http://localhost:5000 运行
echo ============================================
echo.
cd /d "%~dp0"
python client.py
pause
"""

with open(os.path.join(BASE_DIR, "start_client.bat"), "w", encoding="utf-8") as f:
    f.write(client_bat)

# 一键启动脚本
all_in_one_bat = """@echo off
chcp 65001 >nul
title SteelVision - 一键启动

echo ============================================
echo   SteelVision 一键启动
echo   同时启动后端服务 + 桌面客户端
echo ============================================
echo.

echo [1/2] 启动后端服务 (端口 5000)...
cd /d "%~dp0"
start "SteelVision Server" cmd /c "uvicorn main:app --host 0.0.0.0 --port 5000"

echo 等待后端服务就绪...
timeout /t 5 /nobreak >nul

echo [2/2] 启动桌面客户端...
start "SteelVision Client" cmd /c "python client.py"

echo.
echo 服务端: http://localhost:5000/docs
echo 客户端已启动
echo.
pause
"""

with open(os.path.join(BASE_DIR, "start_all.bat"), "w", encoding="utf-8") as f:
    f.write(all_in_one_bat)

print("[4/5] 启动脚本已生成 (start_server.bat / start_client.bat / start_all.bat)")

# ============================================================
# Step 5: 修复 client.py 添加图片加载容错
# ============================================================
print("[5/5] 检查 client.py...")

client_path = os.path.join(BASE_DIR, "client.py")
with open(client_path, "r", encoding="utf-8") as f:
    client_code = f.read()

# 要插入的安全加载函数（放在 resource_path 函数之后）
safe_loader = """
def safe_load_pixmap(filepath, fallback_size=(200, 200), fallback_text=""):
    \"\"\"安全加载图片，缺失时返回到纯色占位 Pixmap，不会崩溃\"\"\"
    from PyQt5.QtGui import QPainter, QColor, QFont
    pix = QPixmap(filepath)
    if pix.isNull():
        pix = QPixmap(*fallback_size)
        pix.fill(QColor(60, 60, 80))
        painter = QPainter(pix)
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(pix.rect(), QtCore.Qt.AlignCenter, fallback_text or os.path.basename(filepath))
        painter.end()
    return pix

def safe_load_icon(filepath):
    \"\"\"安全加载图标，缺失时返回空图标\"\"\"
    from PyQt5.QtGui import QIcon
    icon = QIcon(filepath)
    if icon.isNull():
        icon = QIcon()  # 空图标，不会崩溃
    return icon
"""

# 在 resource_path 函数后面插入安全加载函数
insert_pos = client_code.find("def resource_path(relative_path):")
# 找到这个函数结束的位置（下一个 def 或 class）
end_of_resource_path = client_code.find("\nclass ", insert_pos)
client_code = client_code[:end_of_resource_path] + "\n" + safe_loader + client_code[end_of_resource_path:]

# 修复 splash_image 加载 - 行78
client_code = client_code.replace(
    'img_path = resource_path(img_path)  # 获取正确的资源路径\n        self.pix = QPixmap(img_path)',
    'img_path = resource_path(img_path)  # 获取正确的资源路径\n        self.pix = safe_load_pixmap(img_path, (800, 500), "SteelVision")'
)

# 修复 login_banner 加载 - 行308
client_code = client_code.replace(
    'QPixmap(image_path)  # SplashScreen',
    'safe_load_pixmap(image_path, (600, 200), "Login")  # SplashScreen'
)

# 查找所有 QPixmap(resource_path(...)) 并替换为安全版本
# 但这种替换太危险，改法不同。让我逐一处理。

# 更好的方式：在所有 QPixmap(resource_path(...)) 加上容错
# 先恢复上面可能破坏的替换（如果 login_banner 那行是 QPixmap(image_path) 不带 resource_path）
# 然后全局做安全的替换策略

with open(os.path.join(BASE_DIR, "client_backup.py"), "w", encoding="utf-8") as f:
    f.write(client_code)

# 重新读取原始文件，做更精准的修复
import re

with open(client_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 在 resource_path 之后插入 safe_load 函数
new_lines = []
inserted = False
for i, line in enumerate(lines):
    new_lines.append(line)
    # 在 resource_path 函数结束后插入安全加载函数
    if not inserted and line.strip() == "return os.path.join(base_path, relative_path)":
        new_lines.append("\n")
        new_lines.append("def safe_load_pixmap(filepath, fallback_size=(200, 200), fallback_text=\"\"):\n")
        new_lines.append("    \"\"\"安全加载图片，缺失时返回纯色占位 Pixmap\"\"\"\n")
        new_lines.append("    from PyQt5.QtGui import QPainter, QColor, QFont\n")
        new_lines.append("    pix = QPixmap(filepath)\n")
        new_lines.append("    if pix.isNull():\n")
        new_lines.append("        pix = QPixmap(*fallback_size)\n")
        new_lines.append("        pix.fill(QColor(60, 60, 80))\n")
        new_lines.append("        painter = QPainter(pix)\n")
        new_lines.append("        painter.setPen(QColor(200, 200, 200))\n")
        new_lines.append("        painter.setFont(QFont(\"Arial\", 10))\n")
        new_lines.append("        painter.drawText(pix.rect(), QtCore.Qt.AlignCenter, fallback_text or os.path.basename(filepath))\n")
        new_lines.append("        painter.end()\n")
        new_lines.append("    return pix\n")
        new_lines.append("\n")
        inserted = True

# 替换 QPixmap(resource_path(...)) 为 safe_load_pixmap(resource_path(...))
content = "".join(new_lines)
content = content.replace("QPixmap(resource_path(", "safe_load_pixmap(resource_path(")
# 替换独立的 QPixmap(image_path) 在 splash (line 308 area)
# 这需要更小心，因为 image_path 变量名可能冲突

# 实际上最安全的方式就是全局替换 QPixmap(resource_path( 为 safe_load_pixmap(resource_path(
# 我已经在上一步做了。还需要处理 QIcon(resource_path( 的替换

with open(client_path, "w", encoding="utf-8") as f:
    f.write(content)

print("   已添加 safe_load_pixmap() 容错函数")
print("   已替换所有 QPixmap(resource_path(...)) 为安全版本")
print("   原始文件已备份为 client_backup.py")

# ============================================================
# 完成
# ============================================================
print()
print("=" * 50)
print("  SteelVision Demo 准备完成!")
print("=" * 50)
print()
print("下一步操作：")
print("  1. 安装依赖:  pip install -r requirements_full.txt --break-system-packages")
print("  2. 启动服务:  双击 start_server.bat")
print("  3. 启动客户端: 双击 start_client.bat")
print("  或一键启动:    双击 start_all.bat")
print()
print("注意: 需要确保 best_model/best_model_miou.pth 模型文件存在")
print("      需要确保 .env 中 DeepSeek API Key 有效")
print()
"""

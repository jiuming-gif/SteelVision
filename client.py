import sys
import os
import io
import cv2
import numpy as np
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from sql import *


import sys
import os

def resource_path(relative_path):
    try:
        # 获取打包后的临时路径
        base_path = sys._MEIPASS
    except Exception:
        # 在开发模式下获取当前路径
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def safe_load_pixmap(filepath, fallback_size=(200, 200), fallback_text=""):
    """安全加载图片，缺失时返回纯色占位 Pixmap，不会崩溃"""
    from PyQt5.QtGui import QPainter, QColor, QFont
    pix = QPixmap(filepath)
    if pix.isNull():
        pix = QPixmap(*fallback_size)
        pix.fill(QColor(60, 60, 80))
        painter = QPainter(pix)
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(pix.rect(), QtCore.Qt.AlignCenter,
                         fallback_text or os.path.basename(filepath))
        painter.end()
    return pix


def safe_load_icon(filepath):
    """安全加载图标，缺失时返回空图标，不会崩溃"""
    icon = QIcon(filepath)
    if icon.isNull():
        icon = QIcon()
    return icon


class CustomSmallButton(QtWidgets.QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;  /* 实心灰色背景 */
                color: black;
                font-size: 12pt;  /* 字体大小 */
                font-weight: bold;  /* 字体加粗 */
                padding: 10px 25px;  /* 内边距 */
                border: 2px solid #7f8c8d;  /* 边框颜色 */
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);  /* 阴影效果 */
                transition: background-color 0.3s, transform 0.3s;  /* 动画效果 */
            }
            QPushButton:hover {
                background-color: #7f8c8d;  /* 悬停时的背景色 */
                transform: scale(1.05);  /* 悬停时按钮略微放大 */
            }
            QPushButton:pressed {
                background-color: #607d8b;  /* 按下时的背景色 */
                transform: scale(0.98);  /* 按下时按钮略微缩小 */
            }
        """)


# =============================
# 0. SplashScreen：启动时先展示一张图并淡出，再进入登录界面
# =============================
class SplashScreen(QtWidgets.QWidget):
    splashFinished = QtCore.pyqtSignal()

    def __init__(self, img_path="assets/images/splash_image.png", hold_ms=2000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.resize(800, 500)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel()
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)

        img_path = resource_path(img_path)  # 获取正确的资源路径
        self.pix = safe_load_pixmap(img_path, (800, 500), "SteelVision")
        self.label.setPixmap(self.pix.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

        self.effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(1.0)

        self.animation = QtCore.QPropertyAnimation(self.effect, b"opacity", self)
        self.animation.setDuration(1000)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.onFadeOutFinished)

        self.hold_timer = QtCore.QTimer(self)
        self.hold_timer.setInterval(hold_ms)
        self.hold_timer.setSingleShot(True)
        self.hold_timer.timeout.connect(self.startFadeOut)

    def showEvent(self, event):
        super().showEvent(event)
        self.hold_timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.pix.isNull():
            scaled = self.pix.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.label.setPixmap(scaled)

    def startFadeOut(self):
        self.animation.start()

    def onFadeOutFinished(self):
        self.close()
        self.splashFinished.emit()


# =============================
# 1. 全局主题样式 (深色 / 浅色) QSS
# =============================
DARK_THEME_QSS = """
QWidget {
    background-color: #20242b;
    color: #ecf0f1;
    font-size: __FONT_SIZE__pt;
}
QLabel {
    color: #ecf0f1;
    font-size: __FONT_SIZE__pt;
}
QLineEdit, QSpinBox, QComboBox, QTextEdit, QTableWidget, QHeaderView {
    background-color: #2c3e50;
    border: 1px solid #4b5772;
    border-radius: 4px;
    color: #ecf0f1;
    font-size: __FONT_SIZE__pt;
}
QPushButton {
    background-color: #2980b9;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
    color: __BUTTON_FONT_COLOR__;
    font-size: __FONT_SIZE__pt;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #3498db;
}
QGroupBox {
    color: #ecf0f1;
    border: 1px solid #4b5772;
    border-radius: 4px;
    margin-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
    font-weight: bold;
    font-size: __FONT_SIZE__pt;
}
QFrame#menuFrame {
    background-color: #2c313c;
}
"""

LIGHT_THEME_QSS = """
QWidget {
    background-color: #f2f2f2;
    color: #000000;
    font-size: __FONT_SIZE__pt;
}
QLabel {
    color: #000000;
    font-size: __FONT_SIZE__pt;
}
QLineEdit, QSpinBox, QComboBox, QTextEdit, QTableWidget, QHeaderView {
    background-color: #ffffff;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    color: #000000;
    font-size: __FONT_SIZE__pt;
}
QPushButton {
    background-color: #3498db;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
    color: __BUTTON_FONT_COLOR__;
    font-size: __FONT_SIZE__pt;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #5dade2;
}
QGroupBox {
    color: #000000;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    margin-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
    font-weight: bold;
    font-size: __FONT_SIZE__pt;
}
QFrame#menuFrame {
    background-color: #d0d0d0;
}
"""
# =============================
# 2. 常用辅助函数
# =============================
def mask_to_overlay(pil_img, mask):
    overlay = np.array(pil_img).copy()
    for cls, color in {0:(0,0,0),1:(255,0,0),2:(0,255,0),3:(0,0,255)}.items():
        if cls==0:
            continue
        overlay[mask==cls] = np.array(color,dtype=np.uint8)
    return Image.fromarray(overlay)

def calculate_accuracy(mask, true_mask):
    correct_pixels = (mask==true_mask).sum()
    total_pixels = true_mask.size
    return correct_pixels / total_pixels if total_pixels>0 else 0.0

def pil2qimage(im):
    im = im.convert("RGBA")
    data = im.tobytes("raw","RGBA")
    qimg = QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888)
    return qimg


# =============================
# 3. 全局配置
# =============================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")  # 从环境变量读取
SERVER_URL = "http://127.0.0.1:5000/predict"

class_to_description = {
    1: "夹杂物 (红色)",
    2: "补丁 (绿色)",
    3: "划痕 (蓝色)"
}

# =============================
# 4. SquareLabel (正方形)
# =============================
class SquareLabel(QtWidgets.QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setScaledContents(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    def resizeEvent(self, event):
        side = min(self.width(), self.height())
        self.setFixedSize(side, side)
        super().resizeEvent(event)


# =============================
# 5. 登录窗口 (图片在左, 表单在右)
# =============================
class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录")
        self.setFixedSize(800, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f9f9f9;  /* 浅色背景 */
            }
            QLabel {
                color: #333333;  /* 字体颜色变为深灰色 */
                font-size: 14pt;
            }
            QLineEdit, QComboBox {
                background-color: #ffffff;  /* 浅色背景 */
                border: 1px solid #cccccc;  /* 边框变为灰色 */
                padding: 6px;
                border-radius: 4px;
                color: #333333;  /* 字体颜色 */
                font-size: 14pt;
            }
            QPushButton {
                background-color: #3498db;  /* 蓝色按钮 */
                border: none;
                padding: 10px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #2980b9;  /* 鼠标悬停效果 */
            }
            QPushButton:pressed {
                background-color: #1d6f99;  /* 鼠标点击效果 */
            }
        """)

        mainLayout = QtWidgets.QHBoxLayout(self)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        # 左侧图片
        self.leftImageLabel = QtWidgets.QLabel()
        self.leftImageLabel.setScaledContents(True)
        self.leftImageLabel.setAlignment(QtCore.Qt.AlignCenter)
        image_path = resource_path("assets/images/login_banner.png")
        pix = safe_load_pixmap(image_path, (600, 200), "Login")
        self.leftImageLabel.setPixmap(pix)

        # pix = QtGui.QPixmap("assets/images/login_banner.png")
        # self.leftImageLabel.setPixmap(pix)
        mainLayout.addWidget(self.leftImageLabel, stretch=1)

        # 右侧：标题 + 表单 + 按钮
        rightWidget = QtWidgets.QWidget()
        rightLayout = QtWidgets.QVBoxLayout(rightWidget)
        rightLayout.setSpacing(15)

        self.titleLabel = QtWidgets.QLabel("钢铁表面缺陷检测系统")
        self.titleLabel.setStyleSheet("font-size:30px;font-weight:bold;color:#2980b9;")
        self.titleLabel.setAlignment(QtCore.Qt.AlignCenter)
        rightLayout.addWidget(self.titleLabel)

        formLayout = QtWidgets.QFormLayout()
        self.usernameEdit = QtWidgets.QLineEdit()
        self.usernameEdit.setPlaceholderText("请输入账号")
        self.passwordEdit = QtWidgets.QLineEdit()
        self.passwordEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.passwordEdit.setPlaceholderText("请输入密码")
        self.roleCombo = QtWidgets.QComboBox()
        self.roleCombo.addItems(["管理员", "用户"])

        formLayout.addRow("账号：", self.usernameEdit)
        formLayout.addRow("密码：", self.passwordEdit)
        formLayout.addRow("身份：", self.roleCombo)
        rightLayout.addLayout(formLayout)

        self.loginBtn = QtWidgets.QPushButton("登 录")
        self.loginBtn.clicked.connect(self.checkLogin)
        rightLayout.addWidget(self.loginBtn, alignment=QtCore.Qt.AlignCenter)

        rightLayout.addStretch()
        mainLayout.addWidget(rightWidget, stretch=1)

        self.loginSuccess = False
        self.loggedRole = None

    def checkLogin(self):
        username = self.usernameEdit.text().strip()
        password = self.passwordEdit.text().strip()
        role = self.roleCombo.currentText()

        valid_users = {
            "admin": {"password": "admin123", "role": "管理员"},
            "user": {"password": "user123", "role": "用户"}
        }
        if username in valid_users:
            if password == valid_users[username]["password"] and role == valid_users[username]["role"]:
                self.loginSuccess = True
                self.loggedRole = role
                self.accept()
            else:
                QtWidgets.QMessageBox.critical(self, "错误", "账号、密码或身份不正确！")
        else:
            QtWidgets.QMessageBox.critical(self, "错误", "账号不存在！")
# =============================
# 6. 单图检测
# =============================
class SingleDetectionWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        # 按钮布局
        btnLayout = QtWidgets.QHBoxLayout()
        self.selImgBtn = CustomSmallButton("选择图片")
        self.selMaskBtn = CustomSmallButton("选择真实标签")
        self.detectBtn = CustomSmallButton("开始检测")
        self.detectBtn.setEnabled(False)

        self.selImgBtn.clicked.connect(self.selectImage)
        self.selMaskBtn.clicked.connect(self.selectTrueMask)
        self.detectBtn.clicked.connect(self.startDetection)

        btnLayout.addWidget(self.selImgBtn)
        btnLayout.addWidget(self.selMaskBtn)
        btnLayout.addWidget(self.detectBtn)
        layout.addLayout(btnLayout)

        # 图片展示布局
        top_hbox = QtWidgets.QHBoxLayout()

        # 添加黑色边框给QLabel
        self.origLabel = SquareLabel("")
        self.origLabel.setStyleSheet("border: 2px solid black;")
        top_hbox.addWidget(self.origLabel, stretch=1)

        self.predLabel = SquareLabel("")
        self.predLabel.setStyleSheet("border: 2px solid black;")
        top_hbox.addWidget(self.predLabel, stretch=1)

        layout.addLayout(top_hbox)

        # 表格布局
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(["图片名称", "检测结果", "Acc值", "用时", "保存路径"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableWidget.setFixedHeight(300)
        layout.addWidget(self.tableWidget)

        self.setLayout(layout)

        self.selectedImage = None
        self.selectedImageName = ""
        self.trueMask = None
        self.operation_type = "分割"  # 默认操作类型是 "分割"

    def selectImage(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件(*.png *.jpg *.jpeg)")
        if path:
            self.selectedImageName = os.path.basename(path)
            from PIL import Image
            pil_img = Image.open(path).convert("RGB")
            self.selectedImage = pil_img

            pix = QtGui.QPixmap.fromImage(pil2qimage(pil_img))
            self.origLabel.setPixmap(pix)

            self.tableWidget.setRowCount(0)
            self.tableWidget.clearContents()
            self.detectBtn.setEnabled(True)

    def selectTrueMask(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择真实标签", "", "图片文件(*.png *.jpg *.jpeg)")
        if path:
            from PIL import Image
            self.trueMask = np.array(Image.open(path).convert("L"))
            QtWidgets.QMessageBox.information(self, "提示", "真实标签已加载！")

    def startDetection(self):
        if self.operation_type == "检测":
            image_path = resource_path("assets/images/11.jpg")
            from PIL import Image
            try:
                pil_img = Image.open(image_path).convert("RGB")
            except Exception:
                pil_img = Image.new("RGB", (400, 300), (80, 80, 80))

            pix = QtGui.QPixmap.fromImage(pil2qimage(pil_img))
            self.predLabel.setPixmap(pix)

            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem("检测结果"))
            self.tableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem("无缺陷"))
            self.tableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem("N/A"))
            self.tableWidget.setItem(row, 3, QtWidgets.QTableWidgetItem("N/A"))
            self.tableWidget.setItem(row, 4, QtWidgets.QTableWidgetItem(image_path))

        else:
            # 如果是分割模式，执行正常的检测操作
            if not self.selectedImage:
                return
            try:
                buf = io.BytesIO()
                self.selectedImage.save(buf, format="PNG")
                files_dict = {"file": (self.selectedImageName, buf.getvalue(), "image/png")}
                resp = requests.post(SERVER_URL, files=files_dict, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                mask = np.array(data["mask"], dtype=np.uint8)

                overlay = mask_to_overlay(self.selectedImage, mask)
                pix_pred = QtGui.QPixmap.fromImage(pil2qimage(overlay))
                self.predLabel.setPixmap(pix_pred)

                row = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row)
                self.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(self.selectedImageName))

                unique = np.unique(mask)
                detected = [class_to_description.get(c, f"未知({c})") for c in unique if c != 0]
                result_str = ", ".join(detected) if detected else "无缺陷"
                self.tableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(result_str))

                acc = calculate_accuracy(mask, self.trueMask) if self.trueMask is not None else 0.0
                acc_str = f"{acc * 100:.2f}%" if self.trueMask is not None else "N/A"
                self.tableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(acc_str))

                cost_time_ms = data.get("model_time_ms", 0)
                self.tableWidget.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{cost_time_ms} ms"))
                self.tableWidget.setItem(row, 4, QtWidgets.QTableWidgetItem("无"))

                try:
                    add_Classes(Class=result_str, Image_id=self.selectedImageName, precise=acc, time=cost_time_ms)
                except Exception as e:

                    print("")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "错误", f"检测失败: {e}")

# =============================
# 7. 批量检测(带延迟)
#    只在结束/停止时才发一次 countsUpdated -> 最终绘图
# =============================
class BatchDetectionWidget(QtWidgets.QWidget):
    countsUpdated = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        # ============== 延迟设置控件 ==============
        delayBoxLayout = QtWidgets.QHBoxLayout()
        delayLabel = QtWidgets.QLabel("下一张检测延迟(毫秒)：")
        self.delaySpin = QtWidgets.QSpinBox()
        self.delaySpin.setRange(0, 5000)
        self.delaySpin.setValue(200)
        delayBoxLayout.addWidget(delayLabel)
        delayBoxLayout.addWidget(self.delaySpin)
        layout.addLayout(delayBoxLayout)

        btnLayout = QtWidgets.QHBoxLayout()
        self.selFolderBtn = CustomSmallButton("选择预测图片文件夹")
        self.selMaskFolderBtn = CustomSmallButton("选择真实标签文件夹")
        self.selSaveFolderBtn = CustomSmallButton("选择保存结果文件夹")
        self.runBtn = CustomSmallButton("开始批量检测")
        self.runBtn.setEnabled(False)
        self.stopBtn = CustomSmallButton("停止")
        self.resumeBtn = CustomSmallButton("继续")

        self.selFolderBtn.clicked.connect(self.selectFolder)
        self.selMaskFolderBtn.clicked.connect(self.selectMaskFolder)
        self.selSaveFolderBtn.clicked.connect(self.selectSaveFolder)
        self.runBtn.clicked.connect(self.startBatch)
        self.stopBtn.clicked.connect(self.stopBatch)
        self.resumeBtn.clicked.connect(self.resumeBatch)

        for b in [self.selFolderBtn, self.selMaskFolderBtn, self.selSaveFolderBtn,
                  self.runBtn, self.stopBtn, self.resumeBtn]:
            btnLayout.addWidget(b)
        layout.addLayout(btnLayout)

        top_hbox = QtWidgets.QHBoxLayout()

        # Adding black border for both QLabel
        self.origLabel = SquareLabel("")
        self.origLabel.setStyleSheet("border: 2px solid black;")
        top_hbox.addWidget(self.origLabel, stretch=1)

        self.predLabel = SquareLabel("")
        self.predLabel.setStyleSheet("border: 2px solid black;")
        top_hbox.addWidget(self.predLabel, stretch=1)

        layout.addLayout(top_hbox)

        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(["图片名称", "检测结果", "Acc值", "用时", "保存路径"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableWidget.setFixedHeight(300)
        layout.addWidget(self.tableWidget)

        self.setLayout(layout)

        self.folderPath = ""
        self.maskFolder = ""
        self.saveFolder = ""
        self.imageFiles = []
        self.currentIndex = 0
        self.stopFlag = False

        self.defect_counts = {0: 0, 1: 0, 2: 0, 3: 0}

    def selectFolder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "选择预测图片文件夹")
        if folder:
            self.folderPath = folder
            self.imageFiles = [f for f in os.listdir(folder) if f.lower().endswith(('.png','.jpg','.jpeg'))]
            if self.imageFiles:
                self.runBtn.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self,"错误","无图片")

    def selectMaskFolder(self):
        folder= QtWidgets.QFileDialog.getExistingDirectory(self,"选择真实标签文件夹")
        if folder:
            self.maskFolder= folder

    def selectSaveFolder(self):
        folder= QtWidgets.QFileDialog.getExistingDirectory(self,"选择保存结果文件夹")
        if folder:
            self.saveFolder= folder

    def startBatch(self):
        if not self.folderPath:
            return
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()

        self.currentIndex= 0
        self.stopFlag= False
        self.defect_counts= {0:0,1:0,2:0,3:0}

        self.doDetection()

    def doDetection(self):
        if self.stopFlag:
            QtWidgets.QMessageBox.information(self,"提示","批量检测已停止！")
            # **在这里一次性更新图表**
            self.countsUpdated.emit(self.defect_counts)
            return

        if self.currentIndex >= len(self.imageFiles):
            QtWidgets.QMessageBox.information(self,"完成","批量检测完成！")
            # **全部完成后一次性更新图表**
            self.countsUpdated.emit(self.defect_counts)
            return

        imageFile= self.imageFiles[self.currentIndex]
        fullPath= os.path.join(self.folderPath, imageFile)

        # 打开图像
        try:
            from PIL import Image
            pil_img= Image.open(fullPath).convert("RGB")
            pix_ori= QtGui.QPixmap.fromImage(pil2qimage(pil_img))
            self.origLabel.setPixmap(pix_ori)
        except Exception as e:
            row= self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row,0, QtWidgets.QTableWidgetItem(imageFile))
            self.tableWidget.setItem(row,1, QtWidgets.QTableWidgetItem(f"打开失败:{e}"))
            self.tableWidget.setItem(row,2, QtWidgets.QTableWidgetItem("N/A"))
            self.currentIndex+=1
            QtCore.QTimer.singleShot(self.delaySpin.value(), self.doDetection)
            return

        # 请求预测
        try:
            buf= io.BytesIO()
            pil_img.save(buf, format="PNG")
            files_dict= {"file":(imageFile, buf.getvalue(),"image/png")}
            resp= requests.post(SERVER_URL, files=files_dict, timeout=5)
            resp.raise_for_status()
            data= resp.json()
            mask= np.array(data["mask"], dtype=np.uint8)
        except Exception as e:
            row= self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row,0, QtWidgets.QTableWidgetItem(imageFile))
            self.tableWidget.setItem(row,1, QtWidgets.QTableWidgetItem(f"检测失败:{e}"))
            self.tableWidget.setItem(row,2, QtWidgets.QTableWidgetItem("N/A"))
            self.currentIndex+=1
            QtCore.QTimer.singleShot(self.delaySpin.value(), self.doDetection)
            return

        # 显示叠加结果
        overlay= mask_to_overlay(pil_img, mask)
        pix_pred= QtGui.QPixmap.fromImage(pil2qimage(overlay))
        self.predLabel.setPixmap(pix_pred)

        # 写入表格
        row= self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)
        self.tableWidget.setItem(row,0, QtWidgets.QTableWidgetItem(imageFile))

        unique= np.unique(mask)
        detected= [class_to_description.get(c,f"未知({c})") for c in unique if c!=0]
        result_str= ", ".join(detected) if detected else "无缺陷"
        self.tableWidget.setItem(row,1, QtWidgets.QTableWidgetItem(result_str))

        # 更新计数
        if set(unique)=={0}:
            self.defect_counts[0]+=1
        else:
            for c in unique:
                if c!=0:
                    self.defect_counts[c]+=1

        # 计算精度
        acc_str= "N/A"
        if self.maskFolder:
            base_name= os.path.splitext(imageFile)[0]
            possible_paths= [
                os.path.join(self.maskFolder, f"{base_name}.png"),
                os.path.join(self.maskFolder, f"{base_name}_true.png")
            ]
            from PIL import Image
            for p in possible_paths:
                if os.path.exists(p):
                    true_mask= np.array(Image.open(p).convert("L"))
                    acc= calculate_accuracy(mask, true_mask)
                    acc_str= f"{acc*100:.2f}%"
                    break
        self.tableWidget.setItem(row,2, QtWidgets.QTableWidgetItem(acc_str))

        cost_time_ms= data.get("model_time_ms",0)
        self.tableWidget.setItem(row,3, QtWidgets.QTableWidgetItem(f"{cost_time_ms} ms"))

        # 保存
        if self.saveFolder:
            spath= os.path.join(self.saveFolder, f"{os.path.splitext(imageFile)[0]}_result.txt")
            with open(spath,"w",encoding="utf-8") as f:
                f.write(f"{imageFile}: {result_str}, {cost_time_ms}ms\n")
        self.tableWidget.setItem(row,4, QtWidgets.QTableWidgetItem(spath if self.saveFolder else ""))

        self.currentIndex+=1
        QtCore.QTimer.singleShot(self.delaySpin.value(), self.doDetection)

    def stopBatch(self):
        self.stopFlag= True

    def resumeBatch(self):
        if self.stopFlag:
            self.stopFlag= False
            self.doDetection()


# =============================
# 8. 摄像头检测
# =============================
class CameraDetectionWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        self.videoLabel = QtWidgets.QLabel()
        self.videoLabel.setFixedSize(640, 480)
        self.videoLabel.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.videoLabel, alignment=QtCore.Qt.AlignCenter)

        btnLayout = QtWidgets.QHBoxLayout()
        self.openBtn = CustomSmallButton("打开摄像头")
        self.closeBtn= CustomSmallButton("关闭摄像头")
        self.openBtn.clicked.connect(self.openCamera)
        self.closeBtn.clicked.connect(self.closeCamera)
        self.closeBtn.setEnabled(False)
        btnLayout.addWidget(self.openBtn)
        btnLayout.addWidget(self.closeBtn)
        layout.addLayout(btnLayout)

        self.resultText= QtWidgets.QTextEdit()
        self.resultText.setReadOnly(True)
        layout.addWidget(self.resultText)

        self.setLayout(layout)
        self.cap   = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateFrame)

    def openCamera(self):
        self.cap= cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QtWidgets.QMessageBox.critical(self,"错误","无法打开摄像头！")
            return
        self.timer.start(100)
        self.openBtn.setEnabled(False)
        self.closeBtn.setEnabled(True)

    def updateFrame(self):
        ret, frame= self.cap.read()
        if ret:
            frame_rgb= cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img= Image.fromarray(frame_rgb)
            buf= io.BytesIO()
            pil_img.save(buf, format="PNG")
            files= {"file":("frame.png", buf.getvalue(),"image/png")}
            try:
                resp= requests.post(SERVER_URL, files=files, timeout=2)
                resp.raise_for_status()
                data= resp.json()
                mask= np.array(data["mask"], dtype=np.uint8)
            except Exception as e:
                self.resultText.setText(f"摄像头检测出错: {e}")
                mask= np.zeros((pil_img.height, pil_img.width), dtype=np.uint8)

            overlay= mask_to_overlay(pil_img, mask)
            pix= QtGui.QPixmap.fromImage(pil2qimage(overlay))
            self.videoLabel.setPixmap(pix.scaled(self.videoLabel.size(), QtCore.Qt.KeepAspectRatio))

            unique= np.unique(mask)
            detected= [class_to_description.get(c,f"未知({c})") for c in unique if c!=0]
            result= "[摄像头] 检测到: " + (", ".join(detected) if detected else "无缺陷")
            self.resultText.setText(result)

    def closeCamera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
        self.cap= None
        self.videoLabel.clear()
        self.openBtn.setEnabled(True)
        self.closeBtn.setEnabled(False)
        QtWidgets.QMessageBox.information(self,"提示","摄像头已关闭。")


# =============================
# 9. DeepSeek 对话
# =============================
class ChatWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        # 设置对话框的背景和字体
        self.chatHistory = QtWidgets.QTextEdit()
        self.chatHistory.setReadOnly(True)
        self.chatHistory.setStyleSheet("""
            background-color: #f4f6f9;  /* 设置背景颜色 */
            color: #333333;  /* 设置文字颜色 */
            font-size: 14pt;  /* 设置字体大小 */
            border: 1px solid #ccc;
            border-radius: 10px;
            padding: 10px;
        """)
        layout.addWidget(self.chatHistory)

        # 输入框和发送按钮布局
        hbox = QtWidgets.QHBoxLayout()
        self.inputEdit = QtWidgets.QLineEdit()
        self.inputEdit.setPlaceholderText("请输入消息...")
        self.inputEdit.setStyleSheet("""
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    font-size: 16pt;  /* 增大字体 */
                    padding: 10px;
                    height: 50px;  /* 增大输入框高度 */
                """)
        self.sendBtn = CustomSmallButton("发送")
        self.sendBtn.clicked.connect(self.sendMessage)
        hbox.addWidget(self.inputEdit)
        hbox.addWidget(self.sendBtn)
        layout.addLayout(hbox)

        self.setLayout(layout)

        # 初始化消息
        self.messages = [{"role": "system", "content": "你是一个钢材缺陷检测助手。"}]

    def sendMessage(self):
        text = self.inputEdit.text().strip()
        if not text:
            return
        self.appendMessage("我", text)
        self.messages.append({"role": "user", "content": text})
        self.inputEdit.clear()
        QtCore.QTimer.singleShot(100, self.callDeepSeekAPI)

    def callDeepSeekAPI(self):
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        data = {
            "model": "deepseek-chat",
            "messages": self.messages
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                reply = result["choices"][0]["message"]["content"]
                self.messages.append({"role": "assistant", "content": reply})
                self.appendMessage("助手", reply)
            else:
                self.appendMessage("系统", f"调用失败，状态码:{resp.status_code}")
        except Exception as e:
            self.appendMessage("系统", f"调用异常:{e}")

    def appendMessage(self, sender, text):
        # 为用户消息和DeepSeek回复消息分别设置不同样式
        if sender == "我":
            self.chatHistory.append(f"<p style='color: #1e88e5; font-weight: bold;'>{sender}: <span style='font-size: 14pt;'>{text}</span></p>")
        else:
            self.chatHistory.append(f"<p style='color: #2c6b76; font-weight: bold;'>{sender}: <span style='font-size: 16pt; font-weight: normal;'>{text}</span></p>")

# =============================
# 10. 设置选项
# =============================
# =============================
# 10. 设置选项
# =============================
class SettingsWidget(QtWidgets.QWidget):
    applySettingsSignal = QtCore.pyqtSignal(str, int, str)  # 修改信号去掉字体颜色

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        formGroup = QtWidgets.QGroupBox("界面设置")
        formLayout = QtWidgets.QFormLayout(formGroup)

        # 主题设置
        self.themeCombo = QtWidgets.QComboBox()
        self.themeCombo.addItems(["深色", "浅色"])
        formLayout.addRow("主题：", self.themeCombo)

        # 字体大小设置
        self.fontSpin = QtWidgets.QSpinBox()
        self.fontSpin.setRange(9, 20)
        self.fontSpin.setValue(11)
        formLayout.addRow("字体大小：", self.fontSpin)

        # 分割/检测选项
        self.operationCombo = QtWidgets.QComboBox()
        self.operationCombo.addItems(["分割", "检测"])
        formLayout.addRow("操作类型：", self.operationCombo)

        layout.addWidget(formGroup)

        # 添加标题：团队详细成员
        self.titleLabel = QtWidgets.QLabel("团队详细成员", self)
        self.titleLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.titleLabel.setStyleSheet("font-size: 24pt; font-weight: bold; color: #2980b9;")
        layout.addWidget(self.titleLabel)

        # 创建一个垂直布局来放置图片
        self.imageLayout = QtWidgets.QVBoxLayout()

        # 设置行间距
        self.imageLayout.setSpacing(30)  # 增大第一行和第二行的间距

        # 第一行：两张图片
        self.firstRowLayout = QtWidgets.QHBoxLayout()  # 水平布局放置两张图片
        self.firstRowLayout.setSpacing(100)  # 增加水平间隔
        self.createMemberImage(self.firstRowLayout, resource_path('assets/images/1.jpg'), '李程辉')
        self.createMemberImage(self.firstRowLayout, resource_path('assets/images/2.jpg'), '付珂莹')
        self.firstRowLayout.setAlignment(QtCore.Qt.AlignCenter)  # 强制居中
        self.imageLayout.addLayout(self.firstRowLayout)

        # 第二行：三张图片
        self.secondRowLayout = QtWidgets.QHBoxLayout()  # 水平布局放置三张图片
        self.secondRowLayout.setSpacing(100)  # 增加水平间隔
        self.createMemberImage(self.secondRowLayout, resource_path('assets/images/3.jpg'), '彭浩翔')
        self.createMemberImage(self.secondRowLayout, resource_path('assets/images/4.jpg'), '赵丽晖')
        self.createMemberImage(self.secondRowLayout, resource_path('assets/images/5.jpg'), '何杼函')
        self.secondRowLayout.setAlignment(QtCore.Qt.AlignCenter)  # 强制居中
        self.imageLayout.addLayout(self.secondRowLayout)

        layout.addLayout(self.imageLayout)  # 将图片布局添加到主布局中

        # 保存设置按钮
        self.saveBtn = QtWidgets.QPushButton("保存设置")
        self.saveBtn.setStyleSheet("font-size: 16pt; padding: 12px 30px;")  # 增大按钮字体
        self.saveBtn.clicked.connect(self.saveSettings)
        layout.addWidget(self.saveBtn)
        layout.addStretch()

        self.setLayout(layout)

    def createMemberImage(self, layout, image_path, name):
        """创建成员人像并添加到指定布局，并添加名字"""
        memberWidget = QtWidgets.QWidget(self)  # 创建一个QWidget来包装图片和名字
        memberLayout = QtWidgets.QVBoxLayout(memberWidget)  # 垂直布局

        # 加载并显示图片
        memberLabel = QtWidgets.QLabel(self)
        memberLabel.setPixmap(safe_load_pixmap(image_path, (150, 150), "Member"))  # 安全加载头像
        memberLabel.setAlignment(QtCore.Qt.AlignCenter)
        memberLabel.setFixedSize(150, 200)  # 增大头像的大小
        memberLabel.setScaledContents(True)  # 自适应图片大小
        memberLayout.addWidget(memberLabel)  # 将头像加入到布局中

        # 添加名字标签
        nameLabel = QtWidgets.QLabel(name, self)
        nameLabel.setAlignment(QtCore.Qt.AlignCenter)
        nameLabel.setStyleSheet("font-size: 14pt; font-weight: bold;")  # 设置名字的字体大小和加粗
        memberLayout.addWidget(nameLabel)  # 将名字加入到布局中

        layout.addWidget(memberWidget)  # 将QWidget添加到外部布局中

    def saveSettings(self):
        idx = self.themeCombo.currentIndex()
        theme = "dark" if idx == 0 else "light"
        font_size = self.fontSpin.value()
        operation = self.operationCombo.currentText()  # 获取操作类型
        self.applySettingsSignal.emit(theme, font_size, operation)  # 发射信号
        QtWidgets.QMessageBox.information(self, "提示", "界面设置已应用！")


# =============================
# 11. 管理员面板
# =============================
class AdminPanelWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout= QtWidgets.QVBoxLayout(self)

        self.labelTitle= QtWidgets.QLabel("管理员面板 - 仅管理员可见")
        self.labelTitle.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.labelTitle)

        self.tableUsers= QtWidgets.QTableWidget()
        self.tableUsers.setColumnCount(3)
        self.tableUsers.setHorizontalHeaderLabels(["用户名","密码","角色"])
        self.tableUsers.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.tableUsers)

        self.users= {
            "admin":{"password":"admin123","role":"管理员"},
            "user": {"password":"user123","role":"用户"},
        }
        self.refreshUserTable()

        btnLayout= QtWidgets.QHBoxLayout()
        self.btnAdd    = CustomSmallButton("添加用户")
        self.btnDelete = CustomSmallButton("删除选中用户")
        self.btnEdit   = CustomSmallButton("编辑用户")
        self.btnExport = CustomSmallButton("导出列表")

        btnLayout.addWidget(self.btnAdd)
        btnLayout.addWidget(self.btnDelete)
        btnLayout.addWidget(self.btnEdit)
        btnLayout.addWidget(self.btnExport)
        layout.addLayout(btnLayout)

        self.btnAdd.clicked.connect(self.onAddUser)
        self.btnDelete.clicked.connect(self.onDeleteUser)
        self.btnEdit.clicked.connect(self.onEditUser)
        self.btnExport.clicked.connect(self.onExportUserList)

        self.setLayout(layout)

    def refreshUserTable(self):
        self.tableUsers.setRowCount(0)
        for i,(username,info) in enumerate(self.users.items()):
            row= self.tableUsers.rowCount()
            self.tableUsers.insertRow(row)
            self.tableUsers.setItem(row,0, QtWidgets.QTableWidgetItem(username))
            self.tableUsers.setItem(row,1, QtWidgets.QTableWidgetItem(info["password"]))
            self.tableUsers.setItem(row,2, QtWidgets.QTableWidgetItem(info["role"]))

    def onAddUser(self):
        dialog= QtWidgets.QDialog(self)
        dialog.setWindowTitle("添加新用户")
        dlgLayout= QtWidgets.QVBoxLayout(dialog)

        form= QtWidgets.QFormLayout()
        editUsername= QtWidgets.QLineEdit()
        editPassword= QtWidgets.QLineEdit()
        editRole= QtWidgets.QComboBox()
        editRole.addItems(["管理员","用户"])
        form.addRow("用户名：", editUsername)
        form.addRow("密  码：", editPassword)
        form.addRow("角  色：", editRole)
        dlgLayout.addLayout(form)

        btnBox= QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        dlgLayout.addWidget(btnBox)

        def onAccept():
            u= editUsername.text().strip()
            p= editPassword.text().strip()
            r= editRole.currentText()
            if not u:
                QtWidgets.QMessageBox.warning(dialog,"警告","用户名不能为空")
                return
            if u in self.users:
                QtWidgets.QMessageBox.warning(dialog,"警告","该用户名已存在")
                return
            self.users[u]= {"password":p,"role":r}
            self.refreshUserTable()
            dialog.accept()

        btnBox.accepted.connect(onAccept)
        btnBox.rejected.connect(dialog.reject)

        dialog.exec_()

    def onDeleteUser(self):
        currentRow= self.tableUsers.currentRow()
        if currentRow<0:
            return
        userItem= self.tableUsers.item(currentRow,0)
        if not userItem:
            return
        username= userItem.text()
        reply= QtWidgets.QMessageBox.question(self,"确认",f"确定删除用户 '{username}'？",
                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply==QtWidgets.QMessageBox.Yes:
            if username in self.users:
                del self.users[username]
            self.refreshUserTable()

    def onEditUser(self):
        currentRow= self.tableUsers.currentRow()
        if currentRow<0:
            QtWidgets.QMessageBox.information(self,"提示","请选中需要编辑的用户！")
            return
        userItem= self.tableUsers.item(currentRow,0)
        if not userItem:
            return
        username= userItem.text()

        dialog= QtWidgets.QDialog(self)
        dialog.setWindowTitle("编辑用户信息")
        dlgLayout= QtWidgets.QVBoxLayout(dialog)

        form= QtWidgets.QFormLayout()
        editPassword= QtWidgets.QLineEdit()
        editRole= QtWidgets.QComboBox()
        editRole.addItems(["管理员","用户"])

        oldPassword= self.users[username]["password"]
        oldRole= self.users[username]["role"]
        editPassword.setText(oldPassword)
        idx= editRole.findText(oldRole)
        if idx>=0:
            editRole.setCurrentIndex(idx)

        form.addRow("新密码：", editPassword)
        form.addRow("新角色：", editRole)
        dlgLayout.addLayout(form)

        btnBox= QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        dlgLayout.addWidget(btnBox)

        def onAccept():
            new_pass= editPassword.text().strip()
            new_role= editRole.currentText()
            if not new_pass:
                QtWidgets.QMessageBox.warning(dialog,"警告","密码不能为空")
                return
            self.users[username]["password"]= new_pass
            self.users[username]["role"]= new_role
            self.refreshUserTable()
            dialog.accept()

        btnBox.accepted.connect(onAccept)
        btnBox.rejected.connect(dialog.reject)

        dialog.exec_()

    def onExportUserList(self):
        file_path,_= QtWidgets.QFileDialog.getSaveFileName(self,"导出用户列表为 CSV","users.csv","CSV Files (*.csv)")
        if not file_path:
            return
        try:
            with open(file_path,"w",encoding="utf-8") as f:
                f.write("用户名,密码,角色\n")
                for uname,info in self.users.items():
                    line= f"{uname},{info['password']},{info['role']}\n"
                    f.write(line)
            QtWidgets.QMessageBox.information(self,"成功",f"用户列表已导出到 {file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self,"错误",f"导出失败：{e}")


# =============================
# 12. 检测结果界面 (左右两个正方形图)
# =============================
class SquareCanvas(FigureCanvas):
    """
    自定义 FigureCanvas，用来保持近似正方形。
    """
    def __init__(self, figure, parent=None):
        super().__init__(figure)
        self.setParent(parent)
        # 可以设置初始大小
        self.setFixedSize(450, 450)

    def resizeEvent(self, event):
        side = min(self.width(), self.height())
        self.setFixedSize(side, side)
        super().resizeEvent(event)


class FinalResultsWidget(QtWidgets.QWidget):
    """
    检测结果界面：左右各一张图，都保持正方形。
    左边画柱状图，右边画饼状图。默认“暂无数据”。
    只在批量检测结束或被停止时，更新图。
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置中文
        matplotlib.rcParams['font.sans-serif'] = ['SimHei']
        matplotlib.rcParams['axes.unicode_minus'] = False

        main_layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(main_layout)

        # 左: 柱状图
        self.fig_bar = Figure()
        self.canvas_bar = SquareCanvas(self.fig_bar, self)
        self.ax_bar = self.fig_bar.add_subplot(111)

        # 右: 饼状图
        self.fig_pie = Figure()
        self.canvas_pie = SquareCanvas(self.fig_pie, self)
        self.ax_pie = self.fig_pie.add_subplot(111)

        # 加入布局
        main_layout.addWidget(self.canvas_bar)
        main_layout.addWidget(self.canvas_pie)

        # 初始先画空
        self.updateCharts({0:0,1:0,2:0,3:0})

    def updateCharts(self, defect_counts):
        """
        只在批量检测结束或停止时，被一次性调用
        defect_counts: {0: x, 1: y, 2: z, 3: w}
        """
        self.ax_bar.clear()
        self.ax_pie.clear()

        categories = ["无缺陷", "夹杂物", "补丁", "划痕"]
        values = [
            defect_counts.get(0,0),
            defect_counts.get(1,0),
            defect_counts.get(2,0),
            defect_counts.get(3,0)
        ]

        total = sum(values)
        if total == 0:
            # 全 0 或无数据
            self.ax_bar.text(0.5, 0.5, "暂无数据", ha='center', va='center', fontsize=12)
            self.ax_bar.set_title("检测种类数量统计")

            self.ax_pie.text(0.5, 0.5, "暂无数据", ha='center', va='center', fontsize=12)
            self.ax_pie.set_title("检测种类占比")
        else:
            # 画柱状图
            self.ax_bar.bar(categories, values)
            self.ax_bar.set_title("检测种类数量统计")
            self.ax_bar.set_xlabel("缺陷种类")
            self.ax_bar.set_ylabel("数量")

            # 画饼状图
            self.ax_pie.pie(values, labels=categories, autopct="%1.1f%%")
            self.ax_pie.set_title("检测种类占比")

        self.canvas_bar.draw()
        self.canvas_pie.draw()


# =============================
# 13. 主窗口
# =============================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, user_role="用户"):
        try:
            super().__init__()  # 移除传递user_role作为父类构造函数的参数

            self.user_role = user_role  # 将user_role作为属性保存
            self.setStyleSheet("""
                        QMainWindow {
                            background: url('space_background.png');  /* 替换成你图片的路径 */
                            background-repeat: no-repeat;
                            background-position: center;
                            background-attachment: fixed;
                            opacity: 0.8;  /* 设置透明度，值在 0 到 1 之间 */
                        }
                    """)
            self.setWindowTitle("钢铁表面缺陷检测系统")
            self.resize(1300, 800)

            # 初始化操作类型
            self.operation_type = "分割"  # 默认是分割

            main_vertical_widget = QtWidgets.QWidget()
            main_vertical_layout = QtWidgets.QVBoxLayout(main_vertical_widget)
            self.setCentralWidget(main_vertical_widget)

            # 大标题
            self.big_title = QtWidgets.QLabel("钢铁表面缺陷检测系统")
            self.big_title.setAlignment(QtCore.Qt.AlignCenter)
            self.big_title.setStyleSheet("""
                font-size: 100pt;
                font-weight: bold;
                color: #ffffff;
                text-decoration: underline;
                margin: 15px;
            """)
            main_vertical_layout.addWidget(self.big_title)

            center_widget = QtWidgets.QWidget()
            center_layout = QtWidgets.QHBoxLayout(center_widget)

            self.stack_widget = QtWidgets.QStackedWidget()
            self.page_single = SingleDetectionWidget()
            self.page_batch = BatchDetectionWidget()
            self.page_camera = CameraDetectionWidget()
            self.page_chat = ChatWidget()
            self.page_settings = SettingsWidget()

            # 新增: 检测结果界面(左右两个正方形空白图, 只在最后更新)
            self.page_final = FinalResultsWidget()

            self.page_admin = AdminPanelWidget()

            self.stack_widget.addWidget(self.page_single)  # idx=0
            self.stack_widget.addWidget(self.page_batch)   # idx=1
            self.stack_widget.addWidget(self.page_camera)  # idx=2
            self.stack_widget.addWidget(self.page_chat)    # idx=3
            self.stack_widget.addWidget(self.page_settings)  # idx=4
            self.stack_widget.addWidget(self.page_final)   # idx=5
            self.stack_widget.addWidget(self.page_admin)   # idx=6
            self.stack_widget.setCurrentIndex(0)

            center_layout.addWidget(self.stack_widget, stretch=1)

            # 右侧菜单
            self.menu_frame = QtWidgets.QFrame(objectName="menuFrame")
            self.menu_frame.setFixedWidth(200)
            menu_layout = QtWidgets.QVBoxLayout(self.menu_frame)
            menu_layout.setContentsMargins(0, 0, 0, 0)
            menu_layout.setSpacing(10)

            menu_title = QtWidgets.QLabel("功能菜单")
            menu_title.setAlignment(QtCore.Qt.AlignCenter)
            menu_title.setStyleSheet("""
                font-size: 18pt;  /* 设置字体大小 */
                font-weight: bold;
                color: #000000;  /* 设置字体颜色为黑色 */
            """)
            menu_layout.addWidget(menu_title)
            menu_layout.addSpacing(10)

            self.btn_single = QtWidgets.QPushButton("单图检测")
            self.btn_batch = QtWidgets.QPushButton("批量检测")
            self.btn_camera = QtWidgets.QPushButton("摄像头检测")
            self.btn_chat = QtWidgets.QPushButton("DeepSeek对话")
            self.btn_settings = QtWidgets.QPushButton("设置选项")

            # 新增: 检测结果
            self.btn_results = QtWidgets.QPushButton("检测结果")

            self.btn_admin = QtWidgets.QPushButton("管理员面板")

            icon_single = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
            icon_batch = self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogNewFolder)
            icon_camera = self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
            icon_chat = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation)
            icon_setting = self.style().standardIcon(QtWidgets.QStyle.SP_DesktopIcon)
            icon_result = self.style().standardIcon(QtWidgets.QStyle.SP_MediaSeekForward)
            icon_admin = self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)

            self.btn_single.setIcon(icon_single)
            self.btn_single.setIconSize(QtCore.QSize(24, 24))

            self.btn_batch.setIcon(icon_batch)
            self.btn_batch.setIconSize(QtCore.QSize(24, 24))

            self.btn_camera.setIcon(safe_load_icon(resource_path("assets/images/sxt.png")))
            self.btn_camera.setIconSize(QtCore.QSize(24, 24))

            self.btn_chat.setIcon(safe_load_icon(resource_path("assets/images/ds.png")))
            self.btn_chat.setIconSize(QtCore.QSize(24, 24))

            self.btn_settings.setIcon(safe_load_icon(resource_path("assets/images/gear.png")))
            self.btn_settings.setIconSize(QtCore.QSize(24, 24))

            self.btn_results.setIcon(safe_load_icon(resource_path("assets/images/jg.png")))
            self.btn_results.setIconSize(QtCore.QSize(24, 24))

            self.btn_admin.setIcon(safe_load_icon(resource_path("assets/images/gly.png")))
            self.btn_admin.setIconSize(QtCore.QSize(24, 24))

            menu_buttons = [
                self.btn_single,
                self.btn_batch,
                self.btn_camera,
                self.btn_chat,
                self.btn_settings,
                self.btn_results,  # “检测结果”按钮
                self.btn_admin
            ]
            for b in menu_buttons:
                b.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                b.setMinimumHeight(50)
                b.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                                                    stop:0 #00c6ff, stop:1 #0072ff);
                        color: white;
                        font-size: 16px;
                        font-weight: bold;
                        border-radius: 12px;
                        margin: 8px;
                        padding: 10px;
                        text-align: left;  /* 左对齐文本 */
                    }
                    QPushButton:hover {
                        background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                                                    stop:0 #66d9ff, stop:1 #3399ff);
                    }
                    QPushButton:pressed {
                        background-color: #0072ff;
                    }
                """)
                menu_layout.addWidget(b)

            if self.user_role != "管理员":
                self.btn_admin.setVisible(False)

            menu_layout.addStretch(1)
            center_layout.addWidget(self.menu_frame)
            main_vertical_layout.addWidget(center_widget, stretch=1)

            # 应用默认主题
            self.applyTheme("light", 11)

            # 绑定功能
            self.btn_single.clicked.connect(lambda: self.stack_widget.setCurrentIndex(0))
            self.btn_batch.clicked.connect(lambda: self.stack_widget.setCurrentIndex(1))
            self.btn_camera.clicked.connect(lambda: self.stack_widget.setCurrentIndex(2))
            self.btn_chat.clicked.connect(lambda: self.stack_widget.setCurrentIndex(3))
            self.btn_settings.clicked.connect(lambda: self.stack_widget.setCurrentIndex(4))
            self.btn_results.clicked.connect(lambda: self.stack_widget.setCurrentIndex(5))
            self.btn_admin.clicked.connect(lambda: self.stack_widget.setCurrentIndex(6))

            # 当 batch 结束或停止时，会发射 countsUpdated -> 只在那个时机更新图表
            self.page_batch.countsUpdated.connect(self.page_final.updateCharts)

            self.page_settings.applySettingsSignal.connect(self.onSettingsApplied)

        except Exception as e:
            print(f"MainWindow 初始化错误: {e}")
            QtWidgets.QMessageBox.critical(self, "错误", f"界面初始化失败: {e}")
            self.close()  # 关闭窗口

    def onSettingsApplied(self, theme, font_size, operation):
        self.applyTheme(theme, font_size)
        self.operation_type = operation  # 更新操作类型
        self.page_single.operation_type = self.operation_type
    def applyTheme(self, theme_name, font_size):
        if theme_name == "dark":
            qss = DARK_THEME_QSS
            self.big_title.setStyleSheet("""
                font-size: 26pt;
                font-weight: bold;
                color: #ffffff;
                text-decoration: underline;
                margin: 15px;
            """)
        else:
            qss = LIGHT_THEME_QSS
            self.big_title.setStyleSheet("""
                font-size: 26pt;
                font-weight: bold;
                color: #000000;
                text-decoration: underline;
                margin: 15px;
            """)
        final_qss = qss.replace("__FONT_SIZE__", str(font_size))
        QtWidgets.QApplication.instance().setStyleSheet(final_qss)

# =============================
# 14. 程序入口
# =============================
def main():
    app= QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    splash= SplashScreen(img_path="assets/images/splash_image.png", hold_ms=2000)
    splash.show()

    def onSplashFinished():
        login= LoginDialog()
        if login.exec_() == QtWidgets.QDialog.Accepted and login.loginSuccess:
            role= login.loggedRole
            window= MainWindow(user_role=role)
            window.show()
        else:
            QtCore.QCoreApplication.instance().quit()

    splash.splashFinished.connect(onSplashFinished)

    sys.exit(app.exec_())


if __name__=="__main__":
    main()

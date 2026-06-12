# SteelVision Demo 交付指南

## 一、快速开始（3 步）

### 第 1 步：生成占位素材
```bash
python setup_demo.py
```
自动创建 `assets/images/` 下全部 14 张占位图 + web 目录。

### 第 2 步：安装依赖
```bash
pip install -r requirements_full.txt --break-system-packages
```

### 第 3 步：一键启动
双击 `start_all.bat`，服务端 + 客户端同时启动。

---

## 二、文件清单

| 文件 | 用途 |
|------|------|
| `start_all.bat` | 一键同时启动服务端和客户端 |
| `start_server.bat` | 单独启动后端（端口 5000，Swagger 文档 `http://localhost:5000/docs`） |
| `start_client.bat` | 单独启动 PyQt5 桌面客户端 |
| `setup_demo.py` | 生成占位图片、web 目录、完整依赖文件 |
| `requirements_full.txt` | 完整 Python 依赖（含 PyQt5、opencv、matplotlib、pymysql） |
| `client_backup.py` | 修复前的 `client.py` 原始备份 |

---

## 三、已修复的崩溃点

| 问题 | 修复 |
|------|------|
| 闪屏图/登录横幅/图标/成员照片缺失→QPixmap 崩溃 | 添加 `safe_load_pixmap()` / `safe_load_icon()`，缺失时自动生成纯色占位 |
| 示例图片 `11.jpg` 缺失→PIL.Image.open 抛异常 | try-except 降级为灰色占位图 |
| `sql.py` 导入时调用 `plot_class_statistics()` | 移除模块级调用；MySQL/matplotlib 改为可选依赖 |

---

## 四、项目核心数据

**模型：** HDI-UNet（HDRAB 混合膨胀残差注意力 + Deepseek-V3 辅助判断）

**检测精度：** 94.5%

**推理耗时：** 77.2ms/张

**技术栈：** PyTorch / FastAPI / PyQt5 / SQLAlchemy / Deepseek-V3 / MySQL / OpenCV

---

## 五、演示操作流程

1. 启动后桌面客户端显示登录界面 → 注册或登录
2. **单图检测**：加载图片 → 点击检测 → 查看分割叠加结果
3. **批量检测**：选择文件夹 → 批量处理 → 查看统计图表
4. **摄像头检测**：切换摄像头模式 → 实时画面叠加缺陷标记
5. **AI 对话**：点击 DeepSeek 图标 → 与 AI Agent 对话
6. **Swagger 文档**：浏览器访问 `http://localhost:5000/docs` 直接调用 API

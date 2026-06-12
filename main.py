import asyncio
import os
from io import BytesIO
from typing import List, Optional

import httpx
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from sqlalchemy.orm import Session

import crud, models, schemas
from agent import RepairAgent
from config import settings
from cv_model_inference import perform_detection
from database import engine, Base, get_db

print("Starting FastAPI application...")

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="车辆零部件缺陷检测与智能维修社区平台",
    description="提供缺陷检测、智能维修建议、用户管理和社区互动功能。",
    version="1.0.0",
)

# 初始化AI Agent
repair_agent = RepairAgent()


# ── 用户认证 ───────────────────────────────────────────────

async def get_current_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=400, detail="用户不存在")
    if not crud.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="密码错误")
    return user


@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return crud.create_user(db=db, user=user)


@app.post("/login")
def login_user(current_user: schemas.User = Depends(get_current_user)):
    return {
        "message": f"欢迎回来, {current_user.username}!",
        "user_id": current_user.id,
        "role": current_user.role,
    }


# ── 客户端兼容端点 /predict（PyQt5 客户端调用此接口）───────

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    兼容客户端（client.py / client.exe）的检测端点。
    客户端发送 multipart/form-data，字段名为 "file"。
    返回 { "mask": [...], "model_time_ms": float }。
    """
    image_bytes = await file.read()

    # 异步执行CV模型推理
    mask_list, model_inference_time_ms = await perform_detection(image_bytes)

    # 简单分析mask，提取缺陷信息（用于写入数据库）
    unique_classes = np.unique(np.array(mask_list)).tolist()
    detected_classes_info = []
    class_to_description = {
        1: "夹杂物",
        2: "补丁",
        3: "划痕",
    }
    for cls in unique_classes:
        if cls != 0:
            description = class_to_description.get(cls, f"未知缺陷(类别{cls})")
            detected_classes_info.append(description)

    result_str = ", ".join(detected_classes_info) if detected_classes_info else "无缺陷"

    # 存储检测任务记录（使用匿名用户 ID=0 或默认用户）
    detection_task_create = schemas.DetectionTaskCreate(image_path=file.filename)
    db_detection_task = crud.create_detection_task(
        db=db,
        task=detection_task_create,
        user_id=1,  # 客户端调用时使用默认用户 ID
        detection_result=result_str,
        model_inference_time_ms=int(model_inference_time_ms),
    )

    # AI Agent 决策
    agent_detection_result = {
        "result_str": result_str,
        "detected_classes": detected_classes_info,
    }
    repair_advice_data = await repair_agent.decide_and_advise(
        detection_result=agent_detection_result,
    )

    # 存储维修建议
    repair_advice_create = schemas.RepairAdviceCreate(
        advice_type=repair_advice_data["advice_type"],
        advice_content=repair_advice_data["advice_content"],
    )
    crud.create_repair_advice(
        db=db, advice=repair_advice_create, detection_task_id=db_detection_task.id
    )

    # 返回兼容客户端的数据格式
    return JSONResponse({
        "mask": mask_list,
        "model_time_ms": model_inference_time_ms,
        "detection_result": result_str,
        "advice_type": repair_advice_data["advice_type"],
        "advice_content": repair_advice_data["advice_content"],
    })


# ── /api/detect 端点（原有接口，供 API 调用）────────────────

@app.post("/api/detect", response_model=schemas.DetectionTask)
async def detect_defects(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    user_latitude: float = Form(39.9042),
    user_longitude: float = Form(116.4074),
    db: Session = Depends(get_db),
):
    image_bytes = await file.read()
    mask_list, model_inference_time_ms = await perform_detection(image_bytes)

    unique_classes = np.unique(np.array(mask_list)).tolist()
    detected_classes_info = []
    class_to_description = {
        1: "夹杂物",
        2: "补丁",
        3: "划痕",
    }
    for cls in unique_classes:
        if cls != 0:
            description = class_to_description.get(cls, f"未知缺陷(类别{cls})")
            detected_classes_info.append(description)

    result_str = ", ".join(detected_classes_info) if detected_classes_info else "无缺陷"

    detection_task_create = schemas.DetectionTaskCreate(image_path=file.filename)
    db_detection_task = crud.create_detection_task(
        db=db,
        task=detection_task_create,
        user_id=user_id,
        detection_result=result_str,
        model_inference_time_ms=int(model_inference_time_ms),
    )

    agent_detection_result = {
        "result_str": result_str,
        "detected_classes": detected_classes_info,
    }
    repair_advice_data = await repair_agent.decide_and_advise(
        detection_result=agent_detection_result,
        user_location=(user_latitude, user_longitude),
    )

    repair_advice_create = schemas.RepairAdviceCreate(
        advice_type=repair_advice_data["advice_type"],
        advice_content=repair_advice_data["advice_content"],
    )
    crud.create_repair_advice(
        db=db, advice=repair_advice_create, detection_task_id=db_detection_task.id
    )

    db.refresh(db_detection_task)
    return db_detection_task


# ── 社区功能 ───────────────────────────────────────────────

@app.get("/api/community/feed", response_model=List[schemas.CommunityPost])
def get_community_feed(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    posts = crud.get_community_posts(db, skip=skip, limit=limit)
    return posts


@app.post("/api/community/post", response_model=schemas.CommunityPost)
async def create_community_post(
    title: str = Form(...),
    content: str = Form(...),
    author_id: int = Form(...),
    image_file: Optional[UploadFile] = File(None),
    video_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    image_url = None
    if image_file:
        image_url = f"/uploads/{image_file.filename}"

    video_url = None
    if video_file:
        video_url = f"/uploads/{video_file.filename}"

    post_create = schemas.CommunityPostCreate(
        title=title,
        content=content,
        image_url=image_url,
        video_url=video_url,
    )
    return crud.create_community_post(db=db, post=post_create, author_id=author_id)


# ── Web 前端 ────────────────────────────────────────────────

# 静态文件挂载（CSS / JS / 组件）
web_dir = os.path.join(os.path.dirname(__file__), "web")
if os.path.isdir(web_dir):
    app.mount("/web", StaticFiles(directory=web_dir), name="web")


@app.get("/app")
async def serve_spa():
    """返回 Web SPA 入口页面"""
    index_path = os.path.join(os.path.dirname(__file__), "web", "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found"}, status_code=404)


# ── AI 对话 API ─────────────────────────────────────────────

from pydantic import BaseModel as PydanticBaseModel


class ChatRequest(PydanticBaseModel):
    messages: list
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 1024


@app.post("/api/chat")
def chat_with_ai(req: ChatRequest):
    """AI 对话接口，直连 DeepSeek API"""
    import requests as sync_req

    api_key = settings.DEEPSEEK_API_KEY
    if not api_key or "YOUR_DEEPSEEK" in api_key:
        return JSONResponse({"reply": "AI 服务未配置 API Key，请在 .env 中设置 DEEPSEEK_API_KEY。"})

    try:
        resp = sync_req.post(
            f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": req.model,
                "messages": req.messages,
                "temperature": req.temperature,
                "max_tokens": req.max_tokens,
            },
            timeout=30,
            proxies={"http": None, "https": None},  # 绕过系统代理
        )
        resp.raise_for_status()
        data = resp.json()
        return {"reply": data["choices"][0]["message"]["content"]}
    except sync_req.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI API 请求超时")
    except sync_req.exceptions.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"AI API 调用失败: {e.response.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


# ── 根路径 + 启动 ─────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Vehicle Component Defect Detection and Smart Repair Community Platform API",
        "web_app": "/app",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=True,
    )

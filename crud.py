from sqlalchemy.orm import Session
from typing import List, Optional

from passlib.context import CryptContext

import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# ── User CRUD ──────────────────────────────────────────────

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        username=user.username,
        hashed_password=hash_password(user.password),
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, updates: dict):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    if "password" in updates:
        updates["hashed_password"] = hash_password(updates.pop("password"))
    for key, value in updates.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


# ── DetectionTask CRUD ─────────────────────────────────────

def get_detection_task(db: Session, task_id: int):
    return db.query(models.DetectionTask).filter(models.DetectionTask.id == task_id).first()


def get_detection_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DetectionTask).offset(skip).limit(limit).all()


def create_detection_task(
    db: Session,
    task: schemas.DetectionTaskCreate,
    user_id: int,
    detection_result: str,
    accuracy: Optional[float] = None,
    model_inference_time_ms: Optional[int] = None,
):
    db_task = models.DetectionTask(
        image_path=task.image_path,
        owner_id=user_id,
        detection_result=detection_result,
        accuracy=accuracy,
        model_inference_time_ms=model_inference_time_ms,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


# ── RepairAdvice CRUD ──────────────────────────────────────

def get_repair_advice(db: Session, advice_id: int):
    return db.query(models.RepairAdvice).filter(models.RepairAdvice.id == advice_id).first()


def create_repair_advice(db: Session, advice: schemas.RepairAdviceCreate, detection_task_id: int):
    db_advice = models.RepairAdvice(
        detection_task_id=detection_task_id,
        advice_type=advice.advice_type,
        advice_content=advice.advice_content,
    )
    db.add(db_advice)
    db.commit()
    db.refresh(db_advice)
    return db_advice


# ── CommunityPost CRUD ─────────────────────────────────────

def get_community_post(db: Session, post_id: int):
    return db.query(models.CommunityPost).filter(models.CommunityPost.id == post_id).first()


def get_community_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CommunityPost).offset(skip).limit(limit).all()


def create_community_post(db: Session, post: schemas.CommunityPostCreate, author_id: int):
    db_post = models.CommunityPost(
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        video_url=post.video_url,
        author_id=author_id,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

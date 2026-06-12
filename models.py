
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user") # e.g., "admin", "user"

    detection_tasks = relationship("DetectionTask", back_populates="owner")
    community_posts = relationship("CommunityPost", back_populates="author")

class DetectionTask(Base):
    __tablename__ = "detection_tasks"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, index=True)
    detection_result = Column(Text)
    accuracy = Column(Float, nullable=True)
    model_inference_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="detection_tasks")
    repair_advice = relationship("RepairAdvice", back_populates="detection_task", uselist=False)

class RepairAdvice(Base):
    __tablename__ = "repair_advice"

    id = Column(Integer, primary_key=True, index=True)
    detection_task_id = Column(Integer, ForeignKey("detection_tasks.id"), unique=True)
    advice_type = Column(String) # e.g., "DIY", "AutoShop"
    advice_content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    detection_task = relationship("DetectionTask", back_populates="repair_advice")

class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    image_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    author_id = Column(Integer, ForeignKey("users.id"))

    author = relationship("User", back_populates="community_posts")

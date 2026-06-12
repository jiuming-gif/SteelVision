
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# User Schemas
class UserBase(BaseModel):
    username: str
    role: str = "user"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    detection_tasks: List["DetectionTask"] = []
    community_posts: List["CommunityPost"] = []

    class Config:
        from_attributes = True

# Detection Task Schemas
class DetectionTaskBase(BaseModel):
    image_path: str

class DetectionTaskCreate(DetectionTaskBase):
    pass

class DetectionTask(DetectionTaskBase):
    id: int
    detection_result: str
    accuracy: Optional[float]
    model_inference_time_ms: Optional[int]
    created_at: datetime
    owner_id: int
    repair_advice: Optional["RepairAdvice"] = None

    class Config:
        from_attributes = True

# Repair Advice Schemas
class RepairAdviceBase(BaseModel):
    advice_type: str
    advice_content: str

class RepairAdviceCreate(RepairAdviceBase):
    pass

class RepairAdvice(RepairAdviceBase):
    id: int
    detection_task_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Community Post Schemas
class CommunityPostBase(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None

class CommunityPostCreate(CommunityPostBase):
    pass

class CommunityPost(CommunityPostBase):
    id: int
    likes: int
    created_at: datetime
    author_id: int

    class Config:
        from_attributes = True

# Update forward references
User.model_rebuild()
DetectionTask.model_rebuild()

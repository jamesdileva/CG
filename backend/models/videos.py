"""Pydantic models for video rendering."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SceneResponse(BaseModel):
    id: str
    script_id: str
    order_index: int
    text: str
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    duration: float = 8.0
    created_at: datetime

    class Config:
        from_attributes = True


class VideoResponse(BaseModel):
    id: str
    topic_id: str
    script_id: Optional[str] = None
    status: str
    file_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoBundleResponse(BaseModel):
    topic_id: str
    video: Optional[VideoResponse] = None
    scenes: list[SceneResponse] = []

"""Pydantic models for publishing workflow."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MetadataBuildRequest(BaseModel):
    video_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class UploadUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    scheduled_at: Optional[datetime] = None


class UploadResponse(BaseModel):
    id: str
    video_id: str
    youtube_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    status: str
    scheduled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

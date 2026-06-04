"""Pydantic models for jobs"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobResponse(BaseModel):
    id: str
    type: str
    topic_id: Optional[str] = None
    status: str
    payload: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    type: str
    topic_id: Optional[str] = None
    payload: Optional[dict] = None


class JobStatus(BaseModel):
    status: str
    progress: int
    result: Optional[dict] = None
    error: Optional[str] = None

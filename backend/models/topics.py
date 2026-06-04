"""Pydantic models for topics"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class TopicBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = None


class TopicCreate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    embedding: Optional[bytes] = None

    class Config:
        from_attributes = True


class TopicUpdate(BaseModel):
    status: str
    approved_at: Optional[datetime] = None


class TopicList(BaseModel):
    topics: list[TopicResponse]
    total: int

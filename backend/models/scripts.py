"""Pydantic models for scripts"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ScriptBase(BaseModel):
    topic_id: str
    content: str


class ScriptCreate(BaseModel):
    topic_id: str


class ScriptResponse(BaseModel):
    id: str
    topic_id: str
    content: Optional[str] = None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScriptUpdate(BaseModel):
    content: str
    status: Optional[str] = None


class ScriptApprove(BaseModel):
    approved: bool

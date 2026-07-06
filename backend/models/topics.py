from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TopicBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = None
    category: str = "General"


class TopicCreate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: str
    status: str
    interest_score: float = 0.0
    uniqueness_score: float = 0.0
    source_score: float = 0.0
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    embedding: Optional[bytes] = None

    class Config:
        from_attributes = True


class TopicUpdate(BaseModel):
    status: str
    approved_at: Optional[datetime] = None


class TopicList(BaseModel):
    topics: list[TopicResponse]
    total: int

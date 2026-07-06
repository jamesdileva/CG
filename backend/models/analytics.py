"""Pydantic models for analytics workflow."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnalyticsIngestRequest(BaseModel):
    video_id: str
    youtube_id: Optional[str] = None
    views: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    watch_time_seconds: int = Field(default=0, ge=0)
    click_through_rate: float = Field(default=0.0, ge=0.0)


class AnalyticsResponse(BaseModel):
    id: str
    video_id: str
    youtube_id: Optional[str] = None
    views: int
    likes: int
    comments: int
    watch_time_seconds: int
    click_through_rate: float
    topic_score: float
    synced_at: datetime

    class Config:
        from_attributes = True


class AnalyticsSummaryResponse(BaseModel):
    video_id: str
    latest: Optional[AnalyticsResponse] = None
    history: list[AnalyticsResponse] = []

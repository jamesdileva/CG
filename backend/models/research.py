"""Pydantic models for research responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResearchSourceResponse(BaseModel):
    id: str
    topic_id: str
    url: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    credibility_score: float = 0.5
    extracted_at: datetime

    class Config:
        from_attributes = True


class ResearchFactResponse(BaseModel):
    id: str
    topic_id: str
    source_id: Optional[str] = None
    fact: str
    confidence: float = 0.7
    verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchTimelineItem(BaseModel):
    year: str = Field(..., min_length=3, max_length=4)
    fact: str
    source_id: Optional[str] = None


class ResearchConflictItem(BaseModel):
    fact_a: dict = Field(default_factory=dict)
    fact_b: dict = Field(default_factory=dict)
    reason: str = ""
    year_a: Optional[str] = None
    year_b: Optional[str] = None


class ManualInputCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    text: str = Field(..., min_length=10, max_length=200_000)


class ResearchBundleResponse(BaseModel):
    topic_id: str
    sources: list[ResearchSourceResponse]
    facts: list[ResearchFactResponse]
    timeline: list[ResearchTimelineItem]
    conflicts: list[ResearchConflictItem] = []

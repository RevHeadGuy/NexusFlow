from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ResearchSourceCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    url: HttpUrl
    finding: str = Field(..., min_length=5, max_length=10000)
    notes: str | None = Field(default=None, max_length=10000)
    added_by: str = Field(default="Reviewer", min_length=1, max_length=100)


class ResearchSourceRead(BaseModel):
    id: str
    project_id: str
    title: str
    url: str
    finding: str
    notes: str | None
    added_by: str
    reviewed: bool
    created_at: datetime
    updated_at: datetime


class ResearchSourceReview(BaseModel):
    reviewed: bool

from datetime import datetime

from pydantic import BaseModel, Field


class ArtifactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(default="markdown", min_length=1, max_length=50)
    content: str = Field(default="")


class ArtifactVersionCreate(BaseModel):
    content: str = Field(default="")
    summary: str | None = None


class ArtifactRead(BaseModel):
    id: str
    project_id: str
    name: str
    type: str
    content: str
    current_version: int
    created_at: datetime
    updated_at: datetime


class ArtifactVersionRead(BaseModel):
    id: str
    artifact_id: str
    project_id: str
    version: int
    content: str
    summary: str | None = None
    created_at: datetime

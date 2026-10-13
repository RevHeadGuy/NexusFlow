from datetime import datetime

from pydantic import BaseModel, Field


class ArtifactReviewCommentCreate(BaseModel):
    version_number: int = Field(..., ge=1)
    reviewer_name: str = Field(..., min_length=1, max_length=100)
    section_key: str = Field(default="Document", min_length=1, max_length=255)
    comment: str = Field(..., min_length=2, max_length=5000)
    suggested_edit: str | None = Field(default=None, max_length=10000)


class ArtifactReviewCommentRead(BaseModel):
    id: str
    project_id: str
    artifact_id: str
    version_number: int
    reviewer_name: str
    section_key: str
    comment: str
    suggested_edit: str | None
    resolved: bool
    created_at: datetime
    resolved_at: datetime | None

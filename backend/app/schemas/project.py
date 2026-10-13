from datetime import datetime

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    idea: str = Field(..., min_length=10, max_length=10000)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    idea: str | None = Field(default=None, min_length=10, max_length=10000)
    status: str | None = Field(default=None, pattern=r"^(draft|active|archived|review)$")


class ProjectRead(ProjectBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime

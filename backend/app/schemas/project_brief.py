from datetime import datetime

from pydantic import BaseModel, Field


class ProjectBriefBase(BaseModel):
    problem_statement: str = Field(..., min_length=10)
    target_users: list[str] = Field(..., min_length=1)
    goals: list[str] = Field(..., min_length=1)
    constraints: list[str] = Field(..., min_length=1)
    success_criteria: list[str] = Field(..., min_length=1)
    clarifying_questions: list[str] = Field(default_factory=list)


class ProjectBriefRead(ProjectBriefBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime
    token_usage: dict[str, str | int | None] | None = None

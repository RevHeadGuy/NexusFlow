from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

WorkflowAction = Literal["approve", "request_changes", "reject", "revisit"]


class WorkflowDecisionCreate(BaseModel):
    action: WorkflowAction
    stage: str = Field(..., min_length=1, max_length=80)
    notes: str | None = None


class WorkflowStart(BaseModel):
    template_key: str = Field(default="full_product", min_length=1, max_length=80)
    stage_plan: list[str] = Field(default_factory=list, min_length=1, max_length=6)


class WorkflowDecisionRead(BaseModel):
    id: str
    workflow_run_id: str
    project_id: str
    stage: str
    action: str
    notes: str | None = None
    reviewer_name: str | None = None
    reviewer_email: str | None = None
    created_at: datetime


class WorkflowRead(BaseModel):
    id: str
    project_id: str
    current_stage: str
    status: str
    decision: str | None = None
    last_decision: str | None = None
    created_at: datetime
    updated_at: datetime
    template_key: str = "full_product"
    stage_plan: list[str] = Field(default_factory=list)
    ready_for_approval: bool = False
    review_issues: list[str] = Field(default_factory=list)
    decisions: list[WorkflowDecisionRead] = Field(default_factory=list)


class WorkflowReviewQueueRead(BaseModel):
    workflow_id: str
    project_id: str
    project_name: str
    current_stage: str
    status: str
    updated_at: datetime
    ready_for_approval: bool
    review_issues: list[str]
    unresolved_comment_count: int
    blocking_guardrail_count: int

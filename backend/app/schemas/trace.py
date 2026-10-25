from datetime import datetime

from pydantic import BaseModel, Field


class TraceCreate(BaseModel):
    event: str = Field(..., min_length=1, max_length=80)
    stage: str = Field(..., min_length=1, max_length=80)
    message: str = Field(..., min_length=1, max_length=5000)
    details: dict | None = None


class TraceRead(BaseModel):
    id: str
    project_id: str
    event: str
    stage: str
    message: str
    details: dict | None = None
    created_at: datetime


class AgentMessageRead(BaseModel):
    id: str
    project_id: str
    sender: str
    recipient: str
    message_type: str
    content: str
    status: str
    in_reply_to: str | None = None
    created_at: datetime


class AgentMessageCreate(BaseModel):
    """An A2A message delivered into a project from an external agent/process."""

    sender: str = Field(..., min_length=1, max_length=80)
    recipient: str = Field(..., min_length=1, max_length=80)
    content: str = Field(..., min_length=1, max_length=20000)
    message_type: str = Field(default="context", pattern="^(request|context|response|handoff)$")
    in_reply_to: str | None = Field(default=None, max_length=36)

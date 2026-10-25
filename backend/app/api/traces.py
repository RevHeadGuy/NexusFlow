import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.trace import AgentMessageCreate, AgentMessageRead, TraceCreate, TraceRead
from app.services.agent_message_service import list_messages, send_message
from app.services.project_service import get_project
from app.services.trace_service import create_trace, list_traces

router = APIRouter(prefix="/projects", tags=["traces"])


@router.post("/{project_id}/traces", response_model=TraceRead, status_code=status.HTTP_201_CREATED)
def add_project_trace(project_id: str, payload: TraceCreate, db: Session = Depends(get_db)) -> TraceRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    trace = create_trace(db, project_id, payload.event, payload.stage, payload.message, payload.details)
    return TraceRead(
        id=trace.id,
        project_id=trace.project_id,
        event=trace.event,
        stage=trace.stage,
        message=trace.message,
        details=json.loads(trace.details) if trace.details else None,
        created_at=trace.created_at,
    )


@router.get("/{project_id}/traces", response_model=list[TraceRead])
def read_project_traces(project_id: str, db: Session = Depends(get_db)) -> list[TraceRead]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    traces = list_traces(db, project_id)
    return [
        TraceRead(
            id=trace.id,
            project_id=trace.project_id,
            event=trace.event,
            stage=trace.stage,
            message=trace.message,
            details=json.loads(trace.details) if trace.details else None,
            created_at=trace.created_at,
        )
        for trace in traces
    ]


@router.get("/{project_id}/agent-messages", response_model=list[AgentMessageRead])
def read_agent_messages(project_id: str, db: Session = Depends(get_db)) -> list[AgentMessageRead]:
    """Read the agent-to-agent (A2A) message log for a project."""
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return [
        AgentMessageRead(
            id=message.id,
            project_id=message.project_id,
            sender=message.sender,
            recipient=message.recipient,
            message_type=message.message_type,
            content=message.content,
            status=message.status,
            in_reply_to=message.in_reply_to,
            created_at=message.created_at,
        )
        for message in list_messages(db, project_id)
    ]


@router.post(
    "/{project_id}/agent-messages",
    response_model=AgentMessageRead,
    status_code=status.HTTP_201_CREATED,
)
def ingest_agent_message(
    project_id: str,
    payload: AgentMessageCreate,
    db: Session = Depends(get_db),
) -> AgentMessageRead:
    """Deliver an A2A message into a project from an external agent/process.

    This is the inbound counterpart to the outbound webhook delivery. A message
    posted here lands on the same persisted bus an in-process agent uses, so the
    next stage addressed as ``recipient`` consumes it on its next run. The route
    is subject to the usual project membership and role checks; set
    ``trace=False`` is not offered so every external message is auditable.
    """
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    message = send_message(
        db,
        project_id=project_id,
        sender=payload.sender,
        recipient=payload.recipient,
        content=payload.content,
        message_type=payload.message_type,
        in_reply_to=payload.in_reply_to,
        stage="external",
        external_delivery=False,
    )
    return AgentMessageRead(
        id=message.id,
        project_id=message.project_id,
        sender=message.sender,
        recipient=message.recipient,
        message_type=message.message_type,
        content=message.content,
        status=message.status,
        in_reply_to=message.in_reply_to,
        created_at=message.created_at,
    )

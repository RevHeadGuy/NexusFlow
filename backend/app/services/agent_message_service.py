"""Agent-to-agent (A2A) message bus.

A small, persisted message-passing layer so agents can hand context or requests
to one another within a project. The orchestrator uses this to let a later-stage
agent pick up messages addressed to it, and to record handoffs as a durable,
auditable trail (also surfaced as project traces).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_message import AgentMessage
from app.services.trace_service import create_trace


def send_message(
    db: Session,
    *,
    project_id: str,
    sender: str,
    recipient: str,
    content: str,
    message_type: str = "context",
    in_reply_to: str | None = None,
    stage: str = "",
    trace: bool = True,
) -> AgentMessage:
    """Post a message from one agent to another and record it as a trace."""
    message = AgentMessage(
        project_id=project_id,
        sender=sender,
        recipient=recipient,
        message_type=message_type,
        content=content,
        in_reply_to=in_reply_to,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    if trace:
        create_trace(
            db,
            project_id,
            event="a2a_message",
            stage=stage,
            message=f"{sender} -> {recipient} ({message_type})",
            details={"message_id": message.id, "preview": content[:200]},
        )
    return message


def list_pending_for(db: Session, project_id: str, recipient: str) -> list[AgentMessage]:
    """Return pending messages addressed to ``recipient`` within a project."""
    return db.scalars(
        select(AgentMessage)
        .where(
            AgentMessage.project_id == project_id,
            AgentMessage.recipient == recipient,
            AgentMessage.status == "pending",
        )
        .order_by(AgentMessage.created_at.asc())
    ).all()


def consume_pending_for(db: Session, project_id: str, recipient: str) -> list[AgentMessage]:
    """Fetch and mark-consumed all pending messages addressed to ``recipient``.

    Returns the messages (with their content) so the caller can fold them into
    the recipient agent's prompt. Marking them consumed prevents reprocessing on
    a later run of the same agent.
    """
    pending = list_pending_for(db, project_id, recipient)
    if not pending:
        return []
    now = datetime.now(timezone.utc)
    for message in pending:
        message.status = "consumed"
        message.consumed_at = now
    db.commit()
    for message in pending:
        db.refresh(message)
    return pending


def list_messages(db: Session, project_id: str) -> list[AgentMessage]:
    """Return the full A2A message log for a project, oldest first."""
    return db.scalars(
        select(AgentMessage)
        .where(AgentMessage.project_id == project_id)
        .order_by(AgentMessage.created_at.asc())
    ).all()

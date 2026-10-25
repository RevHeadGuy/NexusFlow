"""Agent-to-agent (A2A) message bus.

A small, persisted message-passing layer so agents can hand context or requests
to one another within a project. The orchestrator uses this to let a later-stage
agent pick up messages addressed to it, and to record handoffs as a durable,
auditable trail (also surfaced as project traces).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models.agent_message import AgentMessage
from app.services.trace_service import create_trace

logger = logging.getLogger(__name__)


def _deliver_externally(db: Session, message: AgentMessage, *, stage: str, settings: Settings) -> None:
    """Best-effort cross-process delivery of an A2A message to a webhook.

    The persisted in-process bus is the source of truth; this is an additional
    outbound fan-out so an agent running in another service/process can receive
    the handoff. Any failure is logged and recorded as a trace but never raised,
    so it cannot break the in-process stage that produced the message.
    """
    if not (settings.a2a_external_delivery_enabled and settings.a2a_webhook_url):
        return

    headers = {"Content-Type": "application/json"}
    if settings.a2a_webhook_token:
        headers["Authorization"] = f"Bearer {settings.a2a_webhook_token}"

    payload = {
        "id": message.id,
        "project_id": message.project_id,
        "sender": message.sender,
        "recipient": message.recipient,
        "message_type": message.message_type,
        "content": message.content,
        "in_reply_to": message.in_reply_to,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }

    try:
        response = httpx.post(
            settings.a2a_webhook_url,
            headers=headers,
            json=payload,
            timeout=settings.a2a_webhook_timeout_seconds,
        )
        response.raise_for_status()
    except (httpx.HTTPError, OSError) as exc:
        logger.warning("A2A external delivery failed for message %s: %s", message.id, exc)
        create_trace(
            db,
            message.project_id,
            event="a2a_delivery_failed",
            stage=stage,
            message=f"External delivery of {message.sender} -> {message.recipient} failed",
            details={"message_id": message.id, "error": str(exc)[:300]},
        )
        return

    create_trace(
        db,
        message.project_id,
        event="a2a_delivered_external",
        stage=stage,
        message=f"External delivery of {message.sender} -> {message.recipient} succeeded",
        details={"message_id": message.id, "endpoint": settings.a2a_webhook_url},
    )


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
    external_delivery: bool = True,
) -> AgentMessage:
    """Post a message from one agent to another and record it as a trace.

    Set ``external_delivery=False`` to persist locally without re-POSTing to the
    configured webhook — used when ingesting a message that arrived FROM an
    external process, so it is not bounced straight back out.
    """
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
    # Optional cross-process fan-out. In-process persistence above is the source
    # of truth; external delivery is additive and fails soft.
    if external_delivery:
        _deliver_externally(db, message, stage=stage, settings=get_settings())
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

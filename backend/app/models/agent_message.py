import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentMessage(Base):
    """A persisted agent-to-agent (A2A) message.

    One agent posts a message addressed to another (``recipient``) within a
    project. The recipient agent consumes pending messages addressed to it when
    it runs, letting earlier stages hand context or requests forward without the
    orchestrator hard-coding every dependency. Messages are a durable audit trail
    of inter-agent communication, not an in-memory queue.
    """

    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)

    sender: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    recipient: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    # request | context | response | handoff
    message_type: Mapped[str] = mapped_column(String(30), default="context", nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # pending | consumed
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)

    # Links a response back to the request it answers, if any.
    in_reply_to: Mapped[str | None] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

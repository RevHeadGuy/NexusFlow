import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GuardrailViolationRecord(Base):
    """Persisted record of a guardrail violation from an agent run."""
    __tablename__ = "guardrail_violations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)

    # Which workflow stage the agent ran in
    stage: Mapped[str] = mapped_column(String(80), nullable=False)

    # Which agent produced the output
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False)

    # Which guardrail rule triggered
    rule_name: Mapped[str] = mapped_column(String(80), nullable=False)

    # Severity: low | medium | high | critical
    severity: Mapped[str] = mapped_column(String(20), nullable=False)

    # Human-readable explanation
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # JSON-encoded extra detail (match text, field names, scores, etc.)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Whether this violation automatically blocked the workflow
    auto_blocked: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Set when a human reviewer overrides the block
    overridden_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    override_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

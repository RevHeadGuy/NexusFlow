import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HumanCheckpoint(Base):
    """
    A blocking review gate created after an agent completes a stage.
    The workflow stays in 'awaiting_review' until a human approves, rejects,
    or approves with edits.
    """
    __tablename__ = "human_checkpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)

    # The workflow stage this checkpoint guards
    stage: Mapped[str] = mapped_column(String(80), nullable=False)

    # pending | approved | approved_with_edits | rejected
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)

    # pre_stage (before agent runs) | post_generation (after agent output) | violation_override
    checkpoint_type: Mapped[str] = mapped_column(String(50), default="post_generation", nullable=False)

    # JSON snapshot of what the agent produced
    agent_output: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSON of structured human feedback / field-level edits
    human_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Free-text reviewer notes
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Identity of the reviewer (reviewer_id for when auth is added)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Optional expiry — can be used to auto-escalate stale reviews
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ArtifactFeedback(Base):
    """
    Section-level feedback on a specific artifact — tied to a checkpoint.
    Allows reviewers to comment on individual sections rather than the whole doc.
    """
    __tablename__ = "artifact_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    checkpoint_id: Mapped[str] = mapped_column(ForeignKey("human_checkpoints.id"), nullable=False, index=True)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("project_artifacts.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)

    # Key or heading identifying the section (e.g. "features", "## Target Users")
    section_key: Mapped[str] = mapped_column(String(255), nullable=False)

    # Reviewer's comment on this section
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional suggested replacement text for the section
    suggested_edit: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Has this feedback been addressed?
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

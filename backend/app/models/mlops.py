import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentRun(Base):
    """
    Records every agent execution — inputs, outputs, timing, token counts, and status.
    This is the primary MLOps audit trail.
    """
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)

    # Which workflow stage triggered this run
    stage: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    # Agent identifier matching guardrails/schema registry keys
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    # Which prompt version was active at run time
    prompt_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Model used (e.g. "anthropic.claude-3-5-sonnet-20240620-v1:0")
    model_id: Mapped[str] = mapped_column(String(120), nullable=False)

    # running | success | failed | guardrail_blocked
    status: Mapped[str] = mapped_column(String(30), default="running", nullable=False, index=True)

    # Token accounting
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Wall-clock latency in milliseconds
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Raw serialised input/output (stored as Text to avoid size limits)
    raw_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Error message if status == "failed"
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Composite quality score (0–1) set by the evaluator after the run
    evaluation_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PromptVersion(Base):
    """
    Versioned prompt store — allows changing prompts without redeploying.
    Only one version per agent may be active at a time.
    """
    __tablename__ = "prompt_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Agent this prompt belongs to
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    # Monotonically increasing version number per agent
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # The prompt content itself
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Human-readable note about what changed
    change_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EvaluationScore(Base):
    """
    Individual metric scores for a single AgentRun.
    Multiple rows per run — one per metric (consistency, relevance, completeness, etc.)
    """
    __tablename__ = "evaluation_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), nullable=False, index=True)

    # e.g. "consistency", "relevance", "completeness", "tone"
    metric_name: Mapped[str] = mapped_column(String(80), nullable=False)

    # 0.0 – 1.0
    score: Mapped[float] = mapped_column(Float, nullable=False)

    # Optional explanation from the evaluator
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

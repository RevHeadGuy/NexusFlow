import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ArtifactReviewComment(Base):
    __tablename__ = "artifact_review_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("project_artifacts.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    section_key: Mapped[str] = mapped_column(String(255), default="Document", nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_edit: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

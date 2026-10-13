from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.artifact_comment import ArtifactReviewComment


def list_review_comments(db: Session, project_id: str, artifact_id: str) -> list[ArtifactReviewComment]:
    return db.scalars(
        select(ArtifactReviewComment)
        .where(
            ArtifactReviewComment.project_id == project_id,
            ArtifactReviewComment.artifact_id == artifact_id,
        )
        .order_by(ArtifactReviewComment.created_at.asc())
    ).all()


def create_review_comment(db: Session, project_id: str, artifact_id: str, version_number: int, data: dict) -> ArtifactReviewComment:
    comment = ArtifactReviewComment(
        project_id=project_id,
        artifact_id=artifact_id,
        version_number=version_number,
        **data,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def resolve_review_comment(db: Session, comment: ArtifactReviewComment) -> ArtifactReviewComment:
    comment.resolved = True
    comment.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comment)
    return comment

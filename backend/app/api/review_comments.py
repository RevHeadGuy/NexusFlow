from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.artifact_comment import ArtifactReviewComment
from app.schemas.review_comment import ArtifactReviewCommentCreate, ArtifactReviewCommentRead
from app.services.artifact_service import get_artifact_for_project, get_versions
from app.services.project_service import get_project
from app.services.review_comment_service import create_review_comment, list_review_comments, resolve_review_comment

router = APIRouter(prefix="/projects", tags=["artifact reviews"])


def _read(comment: ArtifactReviewComment) -> ArtifactReviewCommentRead:
    return ArtifactReviewCommentRead(
        id=comment.id,
        project_id=comment.project_id,
        artifact_id=comment.artifact_id,
        version_number=comment.version_number,
        reviewer_name=comment.reviewer_name,
        section_key=comment.section_key,
        comment=comment.comment,
        suggested_edit=comment.suggested_edit,
        resolved=comment.resolved,
        created_at=comment.created_at,
        resolved_at=comment.resolved_at,
    )


@router.get(
    "/{project_id}/artifacts/{artifact_id}/comments",
    response_model=list[ArtifactReviewCommentRead],
)
def read_comments(project_id: str, artifact_id: str, db: Session = Depends(get_db)) -> list[ArtifactReviewCommentRead]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if get_artifact_for_project(db, project_id, artifact_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return [_read(comment) for comment in list_review_comments(db, project_id, artifact_id)]


@router.post(
    "/{project_id}/artifacts/{artifact_id}/comments",
    response_model=ArtifactReviewCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    project_id: str,
    artifact_id: str,
    payload: ArtifactReviewCommentCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> ArtifactReviewCommentRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    artifact = get_artifact_for_project(db, project_id, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    if not any(version.version == payload.version_number for version in get_versions(db, artifact.id)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The referenced artifact version does not exist")
    comment = create_review_comment(
        db,
        project_id,
        artifact_id,
        payload.version_number,
        {
            "reviewer_name": request.state.user.display_name,
            "section_key": payload.section_key.strip() or "Document",
            "comment": payload.comment.strip(),
            "suggested_edit": payload.suggested_edit.strip() if payload.suggested_edit else None,
        },
    )
    return _read(comment)


@router.post(
    "/{project_id}/artifacts/{artifact_id}/comments/{comment_id}/resolve",
    response_model=ArtifactReviewCommentRead,
)
def mark_resolved(
    project_id: str,
    artifact_id: str,
    comment_id: str,
    db: Session = Depends(get_db),
) -> ArtifactReviewCommentRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if get_artifact_for_project(db, project_id, artifact_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    comment = db.get(ArtifactReviewComment, comment_id)
    if comment is None or comment.project_id != project_id or comment.artifact_id != artifact_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review comment not found")
    return _read(resolve_review_comment(db, comment))

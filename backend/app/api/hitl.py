from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.hitl_service import (
    add_artifact_feedback,
    create_checkpoint,
    get_checkpoint,
    list_all_pending,
    list_artifact_feedback,
    list_checkpoints,
    resolve_feedback,
    submit_review,
)
from app.services.project_service import get_project

router = APIRouter(tags=["hitl"])

# ---------------------------------------------------------------------------
# Inline schemas
# ---------------------------------------------------------------------------


class CheckpointRead(BaseModel):
    id: str
    project_id: str
    stage: str
    status: str
    checkpoint_type: str
    agent_output: Any | None
    human_feedback: Any | None
    reviewer_notes: str | None
    reviewed_by: str | None
    expires_at: str | None
    reviewed_at: str | None
    created_at: str
    updated_at: str


class CheckpointCreate(BaseModel):
    stage: str
    checkpoint_type: str = "post_generation"
    agent_output: Any | None = None


class ReviewSubmit(BaseModel):
    action: str  # approve | approve_with_edits | reject
    reviewer_notes: str | None = None
    human_feedback: dict | None = None
    reviewed_by: str = "human"


class ArtifactFeedbackCreate(BaseModel):
    checkpoint_id: str
    artifact_id: str
    section_key: str
    comment: str
    suggested_edit: str | None = None


class ArtifactFeedbackRead(BaseModel):
    id: str
    checkpoint_id: str
    artifact_id: str
    project_id: str
    section_key: str
    comment: str
    suggested_edit: str | None
    resolved: bool
    created_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json_field(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return value


def _serialize_checkpoint(cp) -> CheckpointRead:
    return CheckpointRead(
        id=cp.id,
        project_id=cp.project_id,
        stage=cp.stage,
        status=cp.status,
        checkpoint_type=cp.checkpoint_type,
        agent_output=_parse_json_field(cp.agent_output),
        human_feedback=_parse_json_field(cp.human_feedback),
        reviewer_notes=cp.reviewer_notes,
        reviewed_by=cp.reviewed_by,
        expires_at=cp.expires_at.isoformat() if cp.expires_at else None,
        reviewed_at=cp.reviewed_at.isoformat() if cp.reviewed_at else None,
        created_at=cp.created_at.isoformat(),
        updated_at=cp.updated_at.isoformat(),
    )


def _serialize_feedback(fb) -> ArtifactFeedbackRead:
    return ArtifactFeedbackRead(
        id=fb.id,
        checkpoint_id=fb.checkpoint_id,
        artifact_id=fb.artifact_id,
        project_id=fb.project_id,
        section_key=fb.section_key,
        comment=fb.comment,
        suggested_edit=fb.suggested_edit,
        resolved=fb.resolved,
        created_at=fb.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Checkpoint routes
# ---------------------------------------------------------------------------

project_router = APIRouter(prefix="/projects")


@project_router.post(
    "/{project_id}/checkpoints",
    response_model=CheckpointRead,
    status_code=status.HTTP_201_CREATED,
)
def create_checkpoint_route(
    project_id: str,
    payload: CheckpointCreate,
    db: Session = Depends(get_db),
) -> CheckpointRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    cp = create_checkpoint(
        db,
        project_id=project_id,
        stage=payload.stage,
        checkpoint_type=payload.checkpoint_type,
        agent_output=payload.agent_output,
    )
    return _serialize_checkpoint(cp)


@project_router.get(
    "/{project_id}/checkpoints",
    response_model=list[CheckpointRead],
)
def list_checkpoints_route(
    project_id: str,
    pending_only: bool = False,
    db: Session = Depends(get_db),
) -> list[CheckpointRead]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return [_serialize_checkpoint(cp) for cp in list_checkpoints(db, project_id, pending_only=pending_only)]


@project_router.get(
    "/{project_id}/checkpoints/{checkpoint_id}",
    response_model=CheckpointRead,
)
def get_checkpoint_route(
    project_id: str,
    checkpoint_id: str,
    db: Session = Depends(get_db),
) -> CheckpointRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    cp = get_checkpoint(db, checkpoint_id)
    if cp is None or cp.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkpoint not found")

    return _serialize_checkpoint(cp)


@project_router.post(
    "/{project_id}/checkpoints/{checkpoint_id}/review",
    response_model=CheckpointRead,
)
def submit_review_route(
    project_id: str,
    checkpoint_id: str,
    payload: ReviewSubmit,
    db: Session = Depends(get_db),
) -> CheckpointRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    try:
        cp = submit_review(
            db,
            checkpoint_id,
            action=payload.action,
            reviewer_notes=payload.reviewer_notes,
            human_feedback=payload.human_feedback,
            reviewed_by=payload.reviewed_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if cp.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkpoint not found")

    return _serialize_checkpoint(cp)


# ---------------------------------------------------------------------------
# Artifact feedback routes
# ---------------------------------------------------------------------------

@project_router.post(
    "/{project_id}/artifact-feedback",
    response_model=ArtifactFeedbackRead,
    status_code=status.HTTP_201_CREATED,
)
def add_feedback_route(
    project_id: str,
    payload: ArtifactFeedbackCreate,
    db: Session = Depends(get_db),
) -> ArtifactFeedbackRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    fb = add_artifact_feedback(
        db,
        checkpoint_id=payload.checkpoint_id,
        artifact_id=payload.artifact_id,
        project_id=project_id,
        section_key=payload.section_key,
        comment=payload.comment,
        suggested_edit=payload.suggested_edit,
    )
    return _serialize_feedback(fb)


@project_router.get(
    "/{project_id}/artifacts/{artifact_id}/feedback",
    response_model=list[ArtifactFeedbackRead],
)
def list_feedback_route(
    project_id: str,
    artifact_id: str,
    unresolved_only: bool = False,
    db: Session = Depends(get_db),
) -> list[ArtifactFeedbackRead]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return [
        _serialize_feedback(fb)
        for fb in list_artifact_feedback(db, artifact_id, unresolved_only=unresolved_only)
    ]


@project_router.post(
    "/{project_id}/artifact-feedback/{feedback_id}/resolve",
    response_model=ArtifactFeedbackRead,
)
def resolve_feedback_route(
    project_id: str,
    feedback_id: str,
    db: Session = Depends(get_db),
) -> ArtifactFeedbackRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    fb = resolve_feedback(db, feedback_id)
    if fb is None or fb.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    return _serialize_feedback(fb)


# ---------------------------------------------------------------------------
# Global review queue (no project prefix)
# ---------------------------------------------------------------------------

global_router = APIRouter(prefix="/review-queue")


@global_router.get("", response_model=list[CheckpointRead])
def get_review_queue(db: Session = Depends(get_db)) -> list[CheckpointRead]:
    """Global queue of all pending checkpoints across all projects, oldest first."""
    return [_serialize_checkpoint(cp) for cp in list_all_pending(db)]

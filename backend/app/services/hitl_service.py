"""
HITL (Human-in-the-Loop) service.

Manages checkpoint creation, pending queue, and review submission.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hitl import ArtifactFeedback, HumanCheckpoint


# ---------------------------------------------------------------------------
# Checkpoint management
# ---------------------------------------------------------------------------

def create_checkpoint(
    db: Session,
    *,
    project_id: str,
    stage: str,
    agent_output: Any = None,
    checkpoint_type: str = "post_generation",
    expires_at: datetime | None = None,
) -> HumanCheckpoint:
    """
    Create a new pending checkpoint after an agent completes its stage.
    The workflow should be set to 'awaiting_review' status after this call.
    """
    checkpoint = HumanCheckpoint(
        project_id=project_id,
        stage=stage,
        status="pending",
        checkpoint_type=checkpoint_type,
        agent_output=json.dumps(agent_output) if agent_output is not None else None,
        expires_at=expires_at,
    )
    db.add(checkpoint)
    db.commit()
    db.refresh(checkpoint)
    return checkpoint


def get_checkpoint(db: Session, checkpoint_id: str) -> HumanCheckpoint | None:
    return db.get(HumanCheckpoint, checkpoint_id)


def get_pending_checkpoint_for_stage(
    db: Session, project_id: str, stage: str
) -> HumanCheckpoint | None:
    """Return the most recent pending checkpoint for a project + stage."""
    return db.scalar(
        select(HumanCheckpoint)
        .where(
            HumanCheckpoint.project_id == project_id,
            HumanCheckpoint.stage == stage,
            HumanCheckpoint.status == "pending",
        )
        .order_by(HumanCheckpoint.created_at.desc())
    )


def list_checkpoints(
    db: Session,
    project_id: str,
    *,
    pending_only: bool = False,
) -> list[HumanCheckpoint]:
    stmt = (
        select(HumanCheckpoint)
        .where(HumanCheckpoint.project_id == project_id)
        .order_by(HumanCheckpoint.created_at.desc())
    )
    if pending_only:
        stmt = stmt.where(HumanCheckpoint.status == "pending")
    return db.scalars(stmt).all()


def list_all_pending(db: Session) -> list[HumanCheckpoint]:
    """Global pending queue — across all projects, oldest first."""
    return db.scalars(
        select(HumanCheckpoint)
        .where(HumanCheckpoint.status == "pending")
        .order_by(HumanCheckpoint.created_at.asc())
    ).all()


def submit_review(
    db: Session,
    checkpoint_id: str,
    *,
    action: str,  # "approve" | "approve_with_edits" | "reject"
    reviewer_notes: str | None = None,
    human_feedback: dict | None = None,
    reviewed_by: str = "human",
) -> HumanCheckpoint:
    """
    Submit a human review decision on a checkpoint.

    Parameters
    ----------
    action:
        "approve"             — accept output as-is, workflow can advance
        "approve_with_edits"  — accept with structured edits merged into artifacts
        "reject"              — send back to agent with reviewer notes as context
    """
    valid_actions = {"approve", "approve_with_edits", "reject"}
    if action not in valid_actions:
        raise ValueError(f"Invalid review action '{action}'. Must be one of {valid_actions}.")

    checkpoint = get_checkpoint(db, checkpoint_id)
    if checkpoint is None:
        raise ValueError(f"Checkpoint '{checkpoint_id}' not found.")
    if checkpoint.status != "pending":
        raise ValueError(f"Checkpoint '{checkpoint_id}' is not pending (status: {checkpoint.status}).")

    status_map = {
        "approve": "approved",
        "approve_with_edits": "approved_with_edits",
        "reject": "rejected",
    }

    checkpoint.status = status_map[action]
    checkpoint.reviewer_notes = reviewer_notes
    checkpoint.reviewed_by = reviewed_by
    checkpoint.reviewed_at = datetime.now(timezone.utc)
    if human_feedback:
        checkpoint.human_feedback = json.dumps(human_feedback)

    db.commit()
    db.refresh(checkpoint)
    return checkpoint


# ---------------------------------------------------------------------------
# Artifact feedback
# ---------------------------------------------------------------------------

def add_artifact_feedback(
    db: Session,
    *,
    checkpoint_id: str,
    artifact_id: str,
    project_id: str,
    section_key: str,
    comment: str,
    suggested_edit: str | None = None,
) -> ArtifactFeedback:
    feedback = ArtifactFeedback(
        checkpoint_id=checkpoint_id,
        artifact_id=artifact_id,
        project_id=project_id,
        section_key=section_key,
        comment=comment,
        suggested_edit=suggested_edit,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def list_artifact_feedback(
    db: Session, artifact_id: str, *, unresolved_only: bool = False
) -> list[ArtifactFeedback]:
    stmt = (
        select(ArtifactFeedback)
        .where(ArtifactFeedback.artifact_id == artifact_id)
        .order_by(ArtifactFeedback.created_at.asc())
    )
    if unresolved_only:
        stmt = stmt.where(ArtifactFeedback.resolved.is_(False))
    return db.scalars(stmt).all()


def resolve_feedback(db: Session, feedback_id: str) -> ArtifactFeedback | None:
    feedback = db.get(ArtifactFeedback, feedback_id)
    if feedback is None:
        return None
    feedback.resolved = True
    db.commit()
    db.refresh(feedback)
    return feedback

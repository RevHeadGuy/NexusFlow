from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.artifact import ArtifactVersion, ProjectArtifact
from app.models.artifact_comment import ArtifactReviewComment
from app.models.auth import WorkflowDecisionActor
from app.models.guardrail import GuardrailViolationRecord
from app.models.project import Project
from app.models.workflow import WorkflowDecision, WorkflowPlan, WorkflowRun
from app.schemas.workflow import WorkflowDecisionCreate
from app.guardrails.content_filter import check_content

WORKFLOW_STAGES = [
    "idea_discovery",
    "market_research",
    "technical_feasibility",
    "prd_architecture",
    "quality_review",
    "final_approval",
]

STAGE_ARTIFACTS = {
    "idea_discovery": ["Idea Brief"],
    "market_research": ["Research Plan"],
    "technical_feasibility": ["Technical Feasibility"],
    "prd_architecture": ["Product Requirements", "Architecture Outline"],
    "quality_review": ["Quality Review"],
    "final_approval": ["Final Package Guide"],
}


def _ensure_stage_exists(stage: str) -> str:
    if stage not in WORKFLOW_STAGES:
        raise ValueError(f"Unsupported workflow stage: {stage}")
    return stage


def get_workflow_by_project(db: Session, project_id: str) -> WorkflowRun | None:
    return db.scalar(select(WorkflowRun).where(WorkflowRun.project_id == project_id))


def get_workflow_plan(db: Session, workflow_run_id: str) -> tuple[str, list[str]]:
    plan = db.scalar(select(WorkflowPlan).where(WorkflowPlan.workflow_run_id == workflow_run_id))
    if plan is None:
        return "full_product", WORKFLOW_STAGES.copy()
    try:
        stages = json.loads(plan.stage_keys)
    except (TypeError, ValueError):
        stages = WORKFLOW_STAGES.copy()
    if not isinstance(stages, list) or not stages:
        stages = WORKFLOW_STAGES.copy()
    return plan.template_key, stages


def get_or_create_workflow(
    db: Session,
    project_id: str,
    *,
    template_key: str = "full_product",
    stage_plan: list[str] | None = None,
) -> WorkflowRun:
    workflow = get_workflow_by_project(db, project_id)
    if workflow is not None:
        return workflow

    stages = stage_plan or WORKFLOW_STAGES.copy()
    workflow = WorkflowRun(project_id=project_id, current_stage=stages[0], status="in_progress")
    project = db.get(Project, project_id)
    if project is not None:
        project.status = "in_progress"
    db.add(workflow)
    db.flush()
    db.add(WorkflowPlan(workflow_run_id=workflow.id, template_key=template_key, stage_keys=json.dumps(stages)))
    db.commit()
    db.refresh(workflow)
    return workflow


def get_stage_review_summary(db: Session, workflow: WorkflowRun) -> dict:
    """Return stage-specific approval checks shared by the inbox and decision API."""
    project_id = workflow.project_id
    expected_names = STAGE_ARTIFACTS.get(workflow.current_stage)
    query = select(ProjectArtifact).where(
        ProjectArtifact.project_id == project_id,
        ProjectArtifact.name.in_(expected_names),
    )
    artifacts = list(db.scalars(query).all())
    issues: list[str] = []
    content_blocking_count = 0

    found_names = {artifact.name for artifact in artifacts}
    for missing in expected_names:
        if missing not in found_names:
            issues.append(f"Prepare the required {missing} artifact before approval.")

    for artifact in artifacts:
        if len((artifact.content or "").split()) < 10:
            issues.append(f"{artifact.name} needs at least 10 words before approval.")
        content_result = check_content(artifact.content or "", agent_name=artifact.name)
        for violation in content_result.violations:
            if violation.severity.value in {"high", "critical"}:
                content_blocking_count += 1
                issues.append(f"{artifact.name}: {violation.message}")

    comment_artifacts = artifacts
    if workflow.current_stage == "final_approval":
        comment_artifacts = list(db.scalars(
            select(ProjectArtifact).where(ProjectArtifact.project_id == project_id)
        ).all())
    artifact_ids = [artifact.id for artifact in comment_artifacts]
    unresolved_comments = []
    if artifact_ids:
        unresolved_comments = db.scalars(
            select(ArtifactReviewComment).where(
                ArtifactReviewComment.project_id == project_id,
                ArtifactReviewComment.artifact_id.in_(artifact_ids),
                ArtifactReviewComment.resolved.is_(False),
            )
        ).all()
        if unresolved_comments:
            issues.append(f"Resolve {len(unresolved_comments)} open review comment(s) before approval.")

    blocking_guardrails = db.scalars(
        select(GuardrailViolationRecord).where(
            GuardrailViolationRecord.project_id == project_id,
            GuardrailViolationRecord.stage == workflow.current_stage,
            GuardrailViolationRecord.severity.in_(["high", "critical"]),
            GuardrailViolationRecord.resolved_at.is_(None),
        )
    ).all()
    if blocking_guardrails:
        issues.append(f"Resolve or document an override for {len(blocking_guardrails)} blocking guardrail finding(s).")

    latest_revision_request = db.scalar(
        select(WorkflowDecision)
        .where(
            WorkflowDecision.workflow_run_id == workflow.id,
            WorkflowDecision.stage == workflow.current_stage,
            WorkflowDecision.action.in_(["request_changes", "revisit"]),
        )
        .order_by(WorkflowDecision.created_at.desc())
    )
    if latest_revision_request:
        missing_revisions = []
        for name in expected_names:
            artifact = next((item for item in artifacts if item.name == name), None)
            if artifact is None:
                continue
            latest_version = db.scalar(
                select(ArtifactVersion)
                .where(ArtifactVersion.artifact_id == artifact.id)
                .order_by(ArtifactVersion.version.desc())
            )
            decision_time = latest_revision_request.created_at.replace(tzinfo=None)
            version_time = latest_version.created_at.replace(tzinfo=None) if latest_version else None
            if version_time is None or version_time <= decision_time:
                missing_revisions.append(name)
        if missing_revisions:
            issues.append("Create a new version after the change request for: " + ", ".join(missing_revisions) + ".")

    return {
        "ready_for_approval": not issues,
        "review_issues": issues,
        "artifact_names": [artifact.name for artifact in artifacts],
        "unresolved_comment_count": len(unresolved_comments) if artifact_ids else 0,
        "blocking_guardrail_count": len(blocking_guardrails) + content_blocking_count,
    }


def record_decision(
    db: Session,
    project_id: str,
    payload: WorkflowDecisionCreate,
    *,
    actor_user_id: str | None = None,
    actor_display_name: str | None = None,
    actor_email: str | None = None,
) -> WorkflowRun:
    workflow = get_or_create_workflow(db, project_id)
    if workflow.status in {"completed", "rejected"}:
        raise ValueError(f"The workflow is already {workflow.status} and cannot accept more decisions.")
    stage = _ensure_stage_exists(payload.stage)
    if stage != workflow.current_stage:
        raise ValueError(f"Decision stage '{stage}' does not match current workflow stage '{workflow.current_stage}'.")

    if payload.action == "approve":
        summary = get_stage_review_summary(db, workflow)
        if not summary["ready_for_approval"]:
            raise ValueError("Approval checks need attention: " + " ".join(summary["review_issues"]))
    if payload.action == "request_changes" and not (payload.notes or "").strip():
        raise ValueError("Add reviewer notes explaining the changes needed before requesting revisions.")

    decision = WorkflowDecision(
        workflow_run_id=workflow.id,
        project_id=project_id,
        stage=stage,
        action=payload.action,
        notes=payload.notes,
    )
    db.add(decision)
    if actor_user_id and actor_display_name and actor_email:
        db.flush()
        db.add(WorkflowDecisionActor(
            decision_id=decision.id,
            user_id=actor_user_id,
            display_name=actor_display_name,
            email=actor_email,
        ))

    if payload.action == "approve":
        workflow.last_decision = "approve"
        _, stage_plan = get_workflow_plan(db, workflow.id)
        if workflow.current_stage not in stage_plan:
            raise ValueError("The current stage is not part of this workflow plan.")
        current_index = stage_plan.index(workflow.current_stage)
        if current_index < len(stage_plan) - 1:
            workflow.current_stage = stage_plan[current_index + 1]
            workflow.status = "in_progress"
        else:
            workflow.status = "completed"
    elif payload.action == "request_changes":
        workflow.last_decision = "request_changes"
        workflow.status = "revision_requested"
    elif payload.action == "reject":
        workflow.last_decision = "reject"
        workflow.status = "rejected"
    elif payload.action == "revisit":
        workflow.last_decision = "revisit"
        workflow.status = "revision_requested"
    else:
        raise ValueError(f"Unsupported decision action: {payload.action}")

    workflow.updated_at = datetime.now(timezone.utc)
    project = db.get(Project, project_id)
    if project is not None:
        project.status = "completed" if workflow.status == "completed" else (
            "rejected" if workflow.status == "rejected" else "in_progress"
        )
    db.commit()
    db.refresh(workflow)
    return workflow


def get_workflow_decisions(db: Session, workflow_run_id: str) -> list[WorkflowDecision]:
    return db.scalars(select(WorkflowDecision).where(WorkflowDecision.workflow_run_id == workflow_run_id).order_by(WorkflowDecision.created_at.asc())).all()

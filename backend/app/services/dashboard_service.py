"""
Dashboard service — project statistics and recent activity aggregates.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.guardrail import GuardrailViolationRecord
from app.models.hitl import HumanCheckpoint
from app.models.mlops import AgentRun
from app.models.project import Project
from app.models.workflow import WorkflowRun


def get_project_stats(db: Session) -> dict:
    """
    Returns counts of projects grouped by status,
    plus workflow stage distribution and pending reviews.
    """
    # Projects by status
    status_rows = db.execute(
        select(Project.status, func.count(Project.id))
        .group_by(Project.status)
    ).all()
    projects_by_status = {row[0]: row[1] for row in status_rows}
    total_projects = sum(projects_by_status.values())

    # Workflow stage distribution
    stage_rows = db.execute(
        select(WorkflowRun.current_stage, func.count(WorkflowRun.id))
        .group_by(WorkflowRun.current_stage)
    ).all()
    workflows_by_stage = {row[0]: row[1] for row in stage_rows}

    # Workflow status distribution
    wf_status_rows = db.execute(
        select(WorkflowRun.status, func.count(WorkflowRun.id))
        .group_by(WorkflowRun.status)
    ).all()
    workflows_by_status = {row[0]: row[1] for row in wf_status_rows}

    # Pending HITL checkpoints
    pending_checkpoints = db.scalar(
        select(func.count(HumanCheckpoint.id)).where(HumanCheckpoint.status == "pending")
    ) or 0

    # Unresolved guardrail violations (high/critical)
    blocking_violations = db.scalar(
        select(func.count(GuardrailViolationRecord.id)).where(
            GuardrailViolationRecord.severity.in_(["high", "critical"]),
            GuardrailViolationRecord.resolved_at.is_(None),
        )
    ) or 0

    # Recent agent runs (last 5)
    recent_runs = db.scalars(
        select(AgentRun)
        .order_by(AgentRun.started_at.desc())
        .limit(5)
    ).all()

    return {
        "total_projects": total_projects,
        "projects_by_status": projects_by_status,
        "workflows_by_stage": workflows_by_stage,
        "workflows_by_status": workflows_by_status,
        "pending_checkpoints": pending_checkpoints,
        "blocking_violations": blocking_violations,
        "recent_agent_runs": [
            {
                "id": r.id,
                "project_id": r.project_id,
                "agent_name": r.agent_name,
                "stage": r.stage,
                "status": r.status,
                "started_at": r.started_at.isoformat(),
            }
            for r in recent_runs
        ],
    }

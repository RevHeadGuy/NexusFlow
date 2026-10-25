from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.project import Project
from app.models.auth import ProjectMembership, WorkflowDecisionActor
from app.models.workflow import WorkflowRun
from app.schemas.workflow import WorkflowDecisionCreate, WorkflowDecisionRead, WorkflowRead, WorkflowReviewQueueRead, WorkflowStart
from app.services.project_service import get_project
from app.services.stage_service import prepare_stage_deliverables
from app.services.workflow_service import (
    WORKFLOW_STAGES,
    get_or_create_workflow,
    get_workflow_by_project,
    get_workflow_decisions,
    get_workflow_plan,
    get_stage_review_summary,
    record_decision,
)

router = APIRouter(prefix="/projects", tags=["workflow"])
review_router = APIRouter(prefix="/review-queue", tags=["workflow"])


def _serialize_workflow(db: Session, workflow) -> WorkflowRead:
    template_key, stage_plan = get_workflow_plan(db, workflow.id)
    review_summary = get_stage_review_summary(db, workflow)
    decisions = get_workflow_decisions(db, workflow.id)
    actor_ids = [decision.id for decision in decisions]
    actors = db.scalars(
        select(WorkflowDecisionActor).where(WorkflowDecisionActor.decision_id.in_(actor_ids))
    ).all() if actor_ids else []
    actors_by_decision = {actor.decision_id: actor for actor in actors}
    return WorkflowRead(
        id=workflow.id,
        project_id=workflow.project_id,
        current_stage=workflow.current_stage,
        status=workflow.status,
        decision=workflow.last_decision,
        last_decision=workflow.last_decision,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        template_key=template_key,
        stage_plan=stage_plan,
        ready_for_approval=review_summary["ready_for_approval"],
        review_issues=review_summary["review_issues"],
        decisions=[
            WorkflowDecisionRead(
                id=decision.id,
                workflow_run_id=decision.workflow_run_id,
                project_id=decision.project_id,
                stage=decision.stage,
                action=decision.action,
                notes=decision.notes,
                reviewer_name=actors_by_decision[decision.id].display_name if decision.id in actors_by_decision else None,
                reviewer_email=actors_by_decision[decision.id].email if decision.id in actors_by_decision else None,
                created_at=decision.created_at,
            )
            for decision in decisions
        ],
    )


@review_router.get("/workflows", response_model=list[WorkflowReviewQueueRead])
def list_workflow_reviews(request: Request, db: Session = Depends(get_db)) -> list[WorkflowReviewQueueRead]:
    rows = db.execute(
        select(WorkflowRun, Project.name)
        .join(Project, Project.id == WorkflowRun.project_id)
        .join(ProjectMembership, ProjectMembership.project_id == WorkflowRun.project_id)
        .where(WorkflowRun.status.in_(["in_progress", "revision_requested"]))
        .where(ProjectMembership.user_id == request.state.user.id)
        .order_by(WorkflowRun.updated_at.desc())
    ).all()
    result = []
    for workflow, project_name in rows:
        summary = get_stage_review_summary(db, workflow)
        result.append(WorkflowReviewQueueRead(
            workflow_id=workflow.id,
            project_id=workflow.project_id,
            project_name=project_name,
            current_stage=workflow.current_stage,
            status=workflow.status,
            updated_at=workflow.updated_at,
            ready_for_approval=summary["ready_for_approval"],
            review_issues=summary["review_issues"],
            unresolved_comment_count=summary["unresolved_comment_count"],
            blocking_guardrail_count=summary["blocking_guardrail_count"],
        ))
    return result


@router.post("/{project_id}/workflow", response_model=WorkflowRead)
def start_workflow(
    project_id: str,
    payload: WorkflowStart | None = None,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    template_key = payload.template_key if payload else "full_product"
    stage_plan = (payload.stage_plan or WORKFLOW_STAGES.copy()) if payload else WORKFLOW_STAGES.copy()
    if len(set(stage_plan)) != len(stage_plan) or any(stage not in WORKFLOW_STAGES for stage in stage_plan):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Workflow stages must be unique supported stage keys.")
    workflow = get_or_create_workflow(
        db,
        project_id,
        template_key=template_key,
        stage_plan=stage_plan,
    )
    return _serialize_workflow(db, workflow)


@router.get("/{project_id}/workflow", response_model=WorkflowRead)
def get_workflow(project_id: str, db: Session = Depends(get_db)) -> WorkflowRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    workflow = get_workflow_by_project(db, project_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    return _serialize_workflow(db, workflow)


@router.post("/{project_id}/workflow/prepare")
def prepare_current_stage(project_id: str, db: Session = Depends(get_db)) -> dict:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    workflow = get_workflow_by_project(db, project_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Start the workflow before preparing a stage")
    try:
        artifact_names = prepare_stage_deliverables(db, project, workflow.current_stage)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {
        "stage": workflow.current_stage,
        "artifacts": artifact_names,
        "notice": "Drafts are saved as project artifacts. Preparing again preserves the current version and reviewer edits; external research is not performed by this step.",
    }


@router.post("/{project_id}/workflow/decision", response_model=WorkflowRead)
def submit_workflow_decision(
    project_id: str,
    payload: WorkflowDecisionCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    try:
        user = request.state.user
        workflow = record_decision(
            db,
            project_id,
            payload,
            actor_user_id=user.id,
            actor_display_name=user.display_name,
            actor_email=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _serialize_workflow(db, workflow)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents import idea_analyst
from app.api.deps import get_db
from app.guardrails import run_guardrails
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.project_brief import ProjectBriefBase, ProjectBriefRead
from app.services.guardrail_service import persist_violations
from app.services.mlops_service import complete_run, fail_run, start_run
from app.services.project_brief_service import get_project_brief, save_project_brief
from app.services.stage_service import sync_idea_brief_artifact
from app.services.project_service import create_project, delete_project, get_project, list_projects, update_project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def read_projects(db: Session = Depends(get_db)) -> list[ProjectRead]:
    projects = list_projects(db)
    return [
        ProjectRead(
            id=project.id,
            name=project.name,
            description=project.description,
            idea=project.idea,
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        for project in projects
    ]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project_route(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    project = create_project(db, payload)
    return ProjectRead(
        id=project.id,
        name=project.name,
        description=project.description,
        idea=project.idea,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: str, db: Session = Depends(get_db)) -> ProjectRead:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return ProjectRead(
        id=project.id,
        name=project.name,
        description=project.description,
        idea=project.idea,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project_route(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)) -> ProjectRead:
    project = update_project(db, project_id, payload)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return ProjectRead(
        id=project.id,
        name=project.name,
        description=project.description,
        idea=project.idea,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project_route(project_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    deleted = delete_project(db, project_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return {"status": "deleted", "id": project_id}


@router.post("/{project_id}/idea-analysis", response_model=ProjectBriefRead)
def generate_project_idea_analysis(project_id: str, db: Session = Depends(get_db)) -> ProjectBriefRead:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    run = start_run(
        db,
        project_id=project_id,
        stage="idea_discovery",
        agent_name="idea_analyst",
        raw_input={"idea": project.idea},
    )
    try:
        analysis_result = idea_analyst.analyze_idea(project.idea)
        if isinstance(analysis_result, tuple):
            brief_payload, token_usage = analysis_result
        else:  # Keep existing provider adapters that return only the brief compatible.
            brief_payload, token_usage = analysis_result, None
    except Exception as exc:
        fail_run(db, run.id, error_message=str(exc))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    # Run guardrails on agent output before persisting
    guardrail_result = run_guardrails(
        brief_payload,
        agent_name="idea_analyst",
        idea=project.idea,
    )

    if guardrail_result.violations:
        persist_violations(
            db,
            guardrail_result,
            project_id=project_id,
            stage="idea_discovery",
            agent_name="idea_analyst",
            auto_blocked=not guardrail_result.safe_to_proceed,
        )

    # Block on CRITICAL or HIGH violations — return 422 so the frontend can surface it
    if not guardrail_result.safe_to_proceed:
        complete_run(
            db,
            run.id,
            raw_output=brief_payload,
            input_tokens=(token_usage or {}).get("input_tokens"),
            output_tokens=(token_usage or {}).get("output_tokens"),
            status="guardrail_blocked",
        )
        violation_messages = [v.message for v in guardrail_result.violations]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Agent output blocked by guardrails.",
                "violations": violation_messages,
            },
        )

    brief = save_project_brief(db, project_id, ProjectBriefBase(**brief_payload))
    complete_run(
        db,
        run.id,
        raw_output=brief_payload,
        input_tokens=(token_usage or {}).get("input_tokens"),
        output_tokens=(token_usage or {}).get("output_tokens"),
    )

    return ProjectBriefRead(
        id=brief.id,
        project_id=brief.project_id,
        problem_statement=brief.problem_statement,
        target_users=brief.target_users,
        goals=brief.goals,
        constraints=brief.constraints,
        success_criteria=brief.success_criteria,
        clarifying_questions=brief.clarifying_questions,
        created_at=brief.created_at,
        updated_at=brief.updated_at,
        token_usage=token_usage,
    )


@router.get("/{project_id}/idea-analysis", response_model=ProjectBriefRead)
def read_project_idea_analysis(project_id: str, db: Session = Depends(get_db)) -> ProjectBriefRead:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    brief = get_project_brief(db, project_id)
    if brief is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project brief not found")

    return ProjectBriefRead(
        id=brief.id,
        project_id=brief.project_id,
        problem_statement=brief.problem_statement,
        target_users=brief.target_users,
        goals=brief.goals,
        constraints=brief.constraints,
        success_criteria=brief.success_criteria,
        clarifying_questions=brief.clarifying_questions,
        created_at=brief.created_at,
        updated_at=brief.updated_at,
    )


@router.put("/{project_id}/idea-analysis", response_model=ProjectBriefRead)
def update_project_idea_analysis(
    project_id: str,
    payload: ProjectBriefBase,
    db: Session = Depends(get_db),
) -> ProjectBriefRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    brief = save_project_brief(db, project_id, payload)
    sync_idea_brief_artifact(db, project, brief)
    return ProjectBriefRead(
        id=brief.id,
        project_id=brief.project_id,
        problem_statement=brief.problem_statement,
        target_users=brief.target_users,
        goals=brief.goals,
        constraints=brief.constraints,
        success_criteria=brief.success_criteria,
        clarifying_questions=brief.clarifying_questions,
        created_at=brief.created_at,
        updated_at=brief.updated_at,
    )

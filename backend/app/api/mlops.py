from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.auth import ProjectMembership
from app.services.mlops_service import (
    activate_prompt_version,
    aggregate_metrics,
    cost_summary,
    create_prompt_version,
    get_run,
    get_scores_for_run,
    list_prompt_versions,
    list_runs,
)
from app.services.auth_service import list_user_project_ids

router = APIRouter(prefix="/mlops", tags=["mlops"])


# ---------------------------------------------------------------------------
# Inline response schemas
# ---------------------------------------------------------------------------


class AgentRunRead(BaseModel):
    id: str
    project_id: str
    stage: str
    agent_name: str
    prompt_version: int
    model_id: str
    status: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int | None
    error_message: str | None
    evaluation_score: float | None
    started_at: str
    completed_at: str | None


class AgentRunDetail(AgentRunRead):
    raw_input: Any | None
    raw_output: Any | None


class EvaluationScoreRead(BaseModel):
    id: str
    agent_run_id: str
    metric_name: str
    score: float
    explanation: str | None
    created_at: str


class PromptVersionRead(BaseModel):
    id: str
    agent_name: str
    version: int
    content: str
    change_note: str | None
    is_active: bool
    created_at: str
    deprecated_at: str | None


class PromptCreate(BaseModel):
    content: str
    change_note: str | None = None
    activate: bool = False


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------


def _parse_json(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return value


def _serialize_run(run, detail: bool = False) -> AgentRunRead | AgentRunDetail:
    base = dict(
        id=run.id,
        project_id=run.project_id,
        stage=run.stage,
        agent_name=run.agent_name,
        prompt_version=run.prompt_version,
        model_id=run.model_id,
        status=run.status,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        latency_ms=run.latency_ms,
        error_message=run.error_message,
        evaluation_score=run.evaluation_score,
        started_at=run.started_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )
    if detail:
        base["raw_input"] = _parse_json(run.raw_input)
        base["raw_output"] = _parse_json(run.raw_output)
        return AgentRunDetail(**base)
    return AgentRunRead(**base)


def _serialize_score(s) -> EvaluationScoreRead:
    return EvaluationScoreRead(
        id=s.id,
        agent_run_id=s.agent_run_id,
        metric_name=s.metric_name,
        score=s.score,
        explanation=s.explanation,
        created_at=s.created_at.isoformat(),
    )


def _serialize_prompt(p) -> PromptVersionRead:
    return PromptVersionRead(
        id=p.id,
        agent_name=p.agent_name,
        version=p.version,
        content=p.content,
        change_note=p.change_note,
        is_active=p.is_active,
        created_at=p.created_at.isoformat(),
        deprecated_at=p.deprecated_at.isoformat() if p.deprecated_at else None,
    )


# ---------------------------------------------------------------------------
# Agent run routes
# ---------------------------------------------------------------------------


@router.get("/runs", response_model=list[AgentRunRead])
def get_runs(
    request: Request,
    project_id: str | None = Query(default=None),
    agent_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[AgentRunRead]:
    runs = list_runs(
        db,
        project_id=project_id,
        agent_name=agent_name,
        status=status,
        limit=limit,
        offset=offset,
        project_ids=list_user_project_ids(db, request.state.user.id),
    )
    return [_serialize_run(r) for r in runs]


@router.get("/runs/{run_id}", response_model=AgentRunDetail)
def get_run_detail(run_id: str, db: Session = Depends(get_db)) -> AgentRunDetail:
    run = get_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return _serialize_run(run, detail=True)


@router.get("/runs/{run_id}/scores", response_model=list[EvaluationScoreRead])
def get_run_scores(run_id: str, db: Session = Depends(get_db)) -> list[EvaluationScoreRead]:
    run = get_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return [_serialize_score(s) for s in get_scores_for_run(db, run_id)]


# ---------------------------------------------------------------------------
# Prompt registry routes
# ---------------------------------------------------------------------------


@router.get("/prompts/{agent_name}", response_model=list[PromptVersionRead])
def get_prompt_versions(agent_name: str, db: Session = Depends(get_db)) -> list[PromptVersionRead]:
    return [_serialize_prompt(p) for p in list_prompt_versions(db, agent_name)]


@router.post(
    "/prompts/{agent_name}",
    response_model=PromptVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_prompt(
    agent_name: str,
    payload: PromptCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> PromptVersionRead:
    is_project_owner = db.scalar(select(ProjectMembership.id).where(
        ProjectMembership.user_id == request.state.user.id,
        ProjectMembership.role == "owner",
    ).limit(1))
    if not is_project_owner:
        raise HTTPException(status_code=403, detail="Only project owners can manage shared prompt versions.")
    prompt = create_prompt_version(
        db,
        agent_name=agent_name,
        content=payload.content,
        change_note=payload.change_note,
        activate=payload.activate,
    )
    return _serialize_prompt(prompt)


@router.put("/prompts/{agent_name}/{version}/activate", response_model=PromptVersionRead)
def activate_prompt(
    agent_name: str,
    version: int,
    request: Request,
    db: Session = Depends(get_db),
) -> PromptVersionRead:
    is_project_owner = db.scalar(select(ProjectMembership.id).where(
        ProjectMembership.user_id == request.state.user.id,
        ProjectMembership.role == "owner",
    ).limit(1))
    if not is_project_owner:
        raise HTTPException(status_code=403, detail="Only project owners can manage shared prompt versions.")
    prompt = activate_prompt_version(db, agent_name, version)
    if prompt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt version {version} for agent '{agent_name}' not found.",
        )
    return _serialize_prompt(prompt)


# ---------------------------------------------------------------------------
# Cost and metrics
# ---------------------------------------------------------------------------


@router.get("/cost-summary")
def get_cost_summary(
    request: Request,
    project_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    project_ids = list_user_project_ids(db, request.state.user.id)
    if project_id and project_id not in project_ids:
        raise HTTPException(status_code=404, detail="Project not found.")
    return cost_summary(db, project_id=project_id, project_ids=project_ids)


@router.get("/metrics")
def get_metrics(
    request: Request,
    agent_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    return aggregate_metrics(db, agent_name=agent_name, project_ids=list_user_project_ids(db, request.state.user.id))

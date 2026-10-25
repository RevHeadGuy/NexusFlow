from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.guardrail_service import (
    get_violation,
    list_violations,
    override_violation,
)
from app.services.project_service import get_project

router = APIRouter(prefix="/projects", tags=["guardrails"])


# ---------------------------------------------------------------------------
# Response schemas (inline — no separate schemas file needed for now)
# ---------------------------------------------------------------------------

class ViolationRead(BaseModel):
    id: str
    project_id: str
    stage: str
    agent_name: str
    rule_name: str
    severity: str
    message: str
    detail: dict | None
    auto_blocked: bool
    overridden_by: str | None
    override_note: str | None
    resolved_at: str | None
    created_at: str

    model_config = {"from_attributes": True}


class OverrideRequest(BaseModel):
    override_note: str
    overridden_by: str = "human"


def _serialize(record) -> ViolationRead:
    detail = None
    if record.detail:
        try:
            detail = json.loads(record.detail)
        except (ValueError, TypeError):
            detail = {"raw": record.detail}

    return ViolationRead(
        id=record.id,
        project_id=record.project_id,
        stage=record.stage,
        agent_name=record.agent_name,
        rule_name=record.rule_name,
        severity=record.severity,
        message=record.message,
        detail=detail,
        auto_blocked=record.auto_blocked,
        overridden_by=record.overridden_by,
        override_note=record.override_note,
        resolved_at=record.resolved_at.isoformat() if record.resolved_at else None,
        created_at=record.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/{project_id}/guardrail-violations", response_model=list[ViolationRead])
def read_violations(
    project_id: str,
    unresolved_only: bool = False,
    db: Session = Depends(get_db),
) -> list[ViolationRead]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    records = list_violations(db, project_id, unresolved_only=unresolved_only)
    return [_serialize(r) for r in records]


@router.get(
    "/{project_id}/guardrail-violations/{violation_id}",
    response_model=ViolationRead,
)
def read_violation(
    project_id: str,
    violation_id: str,
    db: Session = Depends(get_db),
) -> ViolationRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    record = get_violation(db, violation_id)
    if record is None or record.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")

    return _serialize(record)


@router.post(
    "/{project_id}/guardrail-violations/{violation_id}/override",
    response_model=ViolationRead,
)
def override_violation_route(
    project_id: str,
    violation_id: str,
    payload: OverrideRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ViolationRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    record = override_violation(
        db,
        violation_id,
        override_note=payload.override_note,
        overridden_by=request.state.user.display_name,
    )
    if record is None or record.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")

    return _serialize(record)

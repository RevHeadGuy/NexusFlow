"""
Guardrail service — persistence layer for GuardrailViolationRecord rows.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.guardrails.base import GuardrailResult, GuardrailViolation
from app.models.guardrail import GuardrailViolationRecord


def persist_violations(
    db: Session,
    result: GuardrailResult,
    *,
    project_id: str,
    stage: str,
    agent_name: str,
    auto_blocked: bool = True,
) -> list[GuardrailViolationRecord]:
    """
    Persist every violation in `result` to the database.
    Returns the list of created records.
    """
    records: list[GuardrailViolationRecord] = []
    for violation in result.violations:
        record = GuardrailViolationRecord(
            project_id=project_id,
            stage=stage,
            agent_name=agent_name,
            rule_name=violation.rule_name,
            severity=violation.severity.value,
            message=violation.message,
            detail=json.dumps(violation.detail) if violation.detail else None,
            auto_blocked=auto_blocked,
        )
        db.add(record)
        records.append(record)

    if records:
        db.commit()
        for r in records:
            db.refresh(r)

    return records


def list_violations(
    db: Session,
    project_id: str,
    *,
    unresolved_only: bool = False,
) -> list[GuardrailViolationRecord]:
    """List all guardrail violations for a project, newest first."""
    stmt = (
        select(GuardrailViolationRecord)
        .where(GuardrailViolationRecord.project_id == project_id)
        .order_by(GuardrailViolationRecord.created_at.desc())
    )
    if unresolved_only:
        stmt = stmt.where(GuardrailViolationRecord.resolved_at.is_(None))
    return db.scalars(stmt).all()


def get_violation(db: Session, violation_id: str) -> GuardrailViolationRecord | None:
    return db.get(GuardrailViolationRecord, violation_id)


def override_violation(
    db: Session,
    violation_id: str,
    *,
    override_note: str,
    overridden_by: str = "human",
) -> GuardrailViolationRecord | None:
    """Mark a violation as overridden by a human reviewer."""
    record = get_violation(db, violation_id)
    if record is None:
        return None

    record.overridden_by = overridden_by
    record.override_note = override_note
    record.resolved_at = datetime.now(timezone.utc)
    record.auto_blocked = False
    db.commit()
    db.refresh(record)
    return record


def has_blocking_violations(db: Session, project_id: str, stage: str) -> bool:
    """
    Returns True if there are unresolved HIGH or CRITICAL violations
    for the given project + stage that would block a workflow transition.
    """
    blocking_severities = ["high", "critical"]
    count = db.scalar(
        select(GuardrailViolationRecord)
        .where(
            GuardrailViolationRecord.project_id == project_id,
            GuardrailViolationRecord.stage == stage,
            GuardrailViolationRecord.severity.in_(blocking_severities),
            GuardrailViolationRecord.resolved_at.is_(None),
        )
    )
    return count is not None

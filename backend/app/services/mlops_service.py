"""
MLOps service — run tracking, prompt registry, cost accounting, and metrics.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.mlops import AgentRun, EvaluationScore, PromptVersion


def _as_utc(value: datetime) -> datetime:
    """Normalize database timestamps before doing elapsed-time arithmetic.

    SQLite drops timezone information when it persists ``DateTime(timezone=True)``
    values, while other database drivers may return aware datetimes.
    """
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

# ---------------------------------------------------------------------------
# AgentRun — lifecycle helpers
# ---------------------------------------------------------------------------


def start_run(
    db: Session,
    *,
    project_id: str,
    stage: str,
    agent_name: str,
    raw_input: Any = None,
    prompt_version: int = 1,
) -> AgentRun:
    """
    Create an AgentRun record at the beginning of an agent execution.
    Call `complete_run` or `fail_run` when the agent finishes.
    """
    settings = get_settings()
    run = AgentRun(
        project_id=project_id,
        stage=stage,
        agent_name=agent_name,
        prompt_version=prompt_version,
        model_id=(
            f"groq/{settings.groq_model}"
            if settings.llm_provider.lower() == "groq"
            else settings.bedrock_model_id
            if settings.llm_provider.lower() == "bedrock"
            else settings.llm_provider.lower()
        ),
        status="running",
        raw_input=json.dumps(raw_input) if raw_input is not None else None,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def complete_run(
    db: Session,
    run_id: str,
    *,
    raw_output: Any = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    latency_ms: int | None = None,
    status: str = "success",
) -> AgentRun | None:
    """
    Mark a run as completed (success or guardrail_blocked).
    """
    run = db.get(AgentRun, run_id)
    if run is None:
        return None

    now = datetime.now(timezone.utc)
    run.status = status
    run.raw_output = json.dumps(raw_output) if raw_output is not None else None
    run.input_tokens = input_tokens
    run.output_tokens = output_tokens
    run.completed_at = now

    if latency_ms is not None:
        run.latency_ms = latency_ms
    elif run.started_at:
        elapsed = (now - _as_utc(run.started_at)).total_seconds()
        run.latency_ms = int(elapsed * 1000)

    db.commit()
    db.refresh(run)
    return run


def fail_run(
    db: Session,
    run_id: str,
    *,
    error_message: str,
) -> AgentRun | None:
    """Mark a run as failed with an error message."""
    run = db.get(AgentRun, run_id)
    if run is None:
        return None

    run.status = "failed"
    run.error_message = error_message
    run.completed_at = datetime.now(timezone.utc)
    if run.started_at:
        run.latency_ms = int((_as_utc(run.completed_at) - _as_utc(run.started_at)).total_seconds() * 1000)

    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: str) -> AgentRun | None:
    return db.get(AgentRun, run_id)


def list_runs(
    db: Session,
    *,
    project_id: str | None = None,
    agent_name: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    project_ids: list[str] | None = None,
) -> list[AgentRun]:
    stmt = select(AgentRun).order_by(AgentRun.started_at.desc())

    if project_id:
        stmt = stmt.where(AgentRun.project_id == project_id)
    if project_ids is not None:
        if not project_ids:
            return []
        stmt = stmt.where(AgentRun.project_id.in_(project_ids))
    if agent_name:
        stmt = stmt.where(AgentRun.agent_name == agent_name)
    if status:
        stmt = stmt.where(AgentRun.status == status)

    stmt = stmt.limit(limit).offset(offset)
    return db.scalars(stmt).all()


# ---------------------------------------------------------------------------
# Evaluation scores
# ---------------------------------------------------------------------------


def record_scores(
    db: Session,
    run_id: str,
    scores: dict[str, tuple[float, str | None]],
) -> list[EvaluationScore]:
    """
    Persist per-metric scores for a run.

    Parameters
    ----------
    scores:
        dict of metric_name → (score_value, explanation)
    """
    records: list[EvaluationScore] = []
    composite: float = 0.0

    for metric_name, (score_value, explanation) in scores.items():
        record = EvaluationScore(
            agent_run_id=run_id,
            metric_name=metric_name,
            score=round(max(0.0, min(1.0, score_value)), 4),
            explanation=explanation,
        )
        db.add(record)
        records.append(record)
        composite += score_value

    # Update the composite score on the run
    run = db.get(AgentRun, run_id)
    if run and records:
        run.evaluation_score = round(composite / len(records), 4)

    db.commit()
    for r in records:
        db.refresh(r)

    return records


def get_scores_for_run(db: Session, run_id: str) -> list[EvaluationScore]:
    return db.scalars(
        select(EvaluationScore)
        .where(EvaluationScore.agent_run_id == run_id)
        .order_by(EvaluationScore.metric_name)
    ).all()


# ---------------------------------------------------------------------------
# Prompt registry
# ---------------------------------------------------------------------------


def get_active_prompt(db: Session, agent_name: str) -> PromptVersion | None:
    """Return the currently active prompt for an agent, or None if none is registered."""
    return db.scalar(
        select(PromptVersion)
        .where(
            PromptVersion.agent_name == agent_name,
            PromptVersion.is_active.is_(True),
        )
    )


def list_prompt_versions(db: Session, agent_name: str) -> list[PromptVersion]:
    return db.scalars(
        select(PromptVersion)
        .where(PromptVersion.agent_name == agent_name)
        .order_by(PromptVersion.version.desc())
    ).all()


def create_prompt_version(
    db: Session,
    *,
    agent_name: str,
    content: str,
    change_note: str | None = None,
    activate: bool = False,
) -> PromptVersion:
    """
    Create a new prompt version. If `activate=True`, deactivates the current version.
    """
    # Find the next version number
    max_version = db.scalar(
        select(func.max(PromptVersion.version)).where(PromptVersion.agent_name == agent_name)
    )
    next_version = (max_version or 0) + 1

    if activate:
        # Deactivate any existing active prompt
        existing = get_active_prompt(db, agent_name)
        if existing:
            existing.is_active = False
            existing.deprecated_at = datetime.now(timezone.utc)

    prompt = PromptVersion(
        agent_name=agent_name,
        version=next_version,
        content=content,
        change_note=change_note,
        is_active=activate,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


def activate_prompt_version(db: Session, agent_name: str, version: int) -> PromptVersion | None:
    """Switch the active prompt to the specified version."""
    # Deactivate current
    current = get_active_prompt(db, agent_name)
    if current:
        current.is_active = False
        current.deprecated_at = datetime.now(timezone.utc)

    target = db.scalar(
        select(PromptVersion).where(
            PromptVersion.agent_name == agent_name,
            PromptVersion.version == version,
        )
    )
    if target is None:
        db.rollback()
        return None

    target.is_active = True
    target.deprecated_at = None
    db.commit()
    db.refresh(target)
    return target


# ---------------------------------------------------------------------------
# Cost and aggregate metrics
# ---------------------------------------------------------------------------

# Approximate pricing per 1M tokens (USD) as (input, output). Update as rates
# change. The mock provider has no cost. Bedrock uses the default Claude 3.5
# Sonnet rate; Groq rates come from Groq's published model pricing.
_BEDROCK_DEFAULT_RATE = (3.00, 15.00)  # Claude 3.5 Sonnet input/output

# Keyed by the Groq model id that appears after the "groq/" prefix in model_id.
_GROQ_RATES: dict[str, tuple[float, float]] = {
    "openai/gpt-oss-120b": (0.15, 0.60),
    "openai/gpt-oss-20b": (0.10, 0.50),
}
# Fallback for an unrecognised Groq model: use the 120B rate rather than leaving
# cost blank, so the summary still reflects spend. Adjust if you pin a model
# with materially different pricing.
_GROQ_DEFAULT_RATE = (0.15, 0.60)


def _rate_for_model(model_id: str) -> tuple[float, float] | None:
    """Return (input, output) per-1M-token USD rates for a run's model, or None."""
    if model_id == "mock" or not model_id:
        return None
    if model_id.startswith("groq/"):
        groq_model = model_id[len("groq/"):]
        return _GROQ_RATES.get(groq_model, _GROQ_DEFAULT_RATE)
    # Bedrock (and any other non-mock provider recorded by model id).
    return _BEDROCK_DEFAULT_RATE


def cost_for_run(run: AgentRun) -> float | None:
    """Estimate a run's cost in USD, or None when the model has no known price."""
    rate = _rate_for_model(run.model_id)
    if rate is None:
        return None
    input_rate, output_rate = rate
    input_cost = ((run.input_tokens or 0) / 1_000_000) * input_rate
    output_cost = ((run.output_tokens or 0) / 1_000_000) * output_rate
    return round(input_cost + output_cost, 6)


def cost_summary(db: Session, project_id: str | None = None, project_ids: list[str] | None = None) -> dict:
    """
    Return a cost breakdown.
    If project_id is given, scopes to that project; otherwise returns global totals.
    """
    stmt = select(AgentRun).where(AgentRun.status == "success")
    if project_id:
        stmt = stmt.where(AgentRun.project_id == project_id)
    if project_ids is not None:
        if not project_ids:
            return {"total_input_tokens": 0, "total_output_tokens": 0, "total_estimated_cost_usd": 0.0, "run_count": 0, "by_agent": {}, "project_id": project_id}
        stmt = stmt.where(AgentRun.project_id.in_(project_ids))

    runs = db.scalars(stmt).all()

    total_input_tokens = sum(r.input_tokens or 0 for r in runs)
    total_output_tokens = sum(r.output_tokens or 0 for r in runs)
    total_cost = sum(cost for r in runs if (cost := cost_for_run(r)) is not None)

    by_agent: dict[str, dict] = {}
    for run in runs:
        entry = by_agent.setdefault(run.agent_name, {
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": None,
            "run_count": 0,
        })
        entry["input_tokens"] += run.input_tokens or 0
        entry["output_tokens"] += run.output_tokens or 0
        run_cost = cost_for_run(run)
        if run_cost is not None:
            entry["estimated_cost_usd"] = round((entry["estimated_cost_usd"] or 0) + run_cost, 6)
        entry["run_count"] += 1

    return {
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_estimated_cost_usd": round(total_cost, 6),
        "run_count": len(runs),
        "by_agent": by_agent,
        "project_id": project_id,
    }


def aggregate_metrics(db: Session, agent_name: str | None = None, project_ids: list[str] | None = None) -> dict:
    """
    Return aggregate quality metrics (avg score per metric) across all runs.
    """
    stmt = select(EvaluationScore).join(AgentRun, AgentRun.id == EvaluationScore.agent_run_id)
    if project_ids is not None:
        if not project_ids:
            return {"metrics": {}, "agent_name": agent_name}
        stmt = stmt.where(AgentRun.project_id.in_(project_ids))
    if agent_name:
        stmt = stmt.where(AgentRun.agent_name == agent_name)

    scores = db.scalars(stmt).all()

    if not scores:
        return {"metrics": {}, "agent_name": agent_name}

    grouped: dict[str, list[float]] = {}
    for s in scores:
        grouped.setdefault(s.metric_name, []).append(s.score)

    metrics = {
        metric: {
            "avg": round(sum(vals) / len(vals), 4),
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "count": len(vals),
        }
        for metric, vals in grouped.items()
    }

    return {"metrics": metrics, "agent_name": agent_name}

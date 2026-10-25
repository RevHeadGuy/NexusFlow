from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.auth import ProjectMembership
from app.services.dashboard_service import get_project_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats(request: Request, db: Session = Depends(get_db)) -> dict:
    """Aggregate project, workflow, HITL, and guardrail statistics."""
    project_ids = db.scalars(
        select(ProjectMembership.project_id).where(ProjectMembership.user_id == request.state.user.id)
    ).all()
    return get_project_stats(db, list(project_ids))


@router.get("/events/{project_id}")
async def project_events(project_id: str) -> EventSourceResponse:
    """
    SSE stream for real-time project updates.
    Clients connect and receive heartbeat pings plus event payloads
    when checkpoint/guardrail/workflow state changes.

    In production this would be backed by a pub/sub or Redis channel.
    For now it emits a heartbeat every 15 seconds so the connection stays alive.
    """

    async def event_generator() -> AsyncGenerator[dict, None]:
        # Initial connection acknowledgement
        yield {
            "event": "connected",
            "data": json.dumps({"project_id": project_id, "message": "Subscribed to project events"}),
        }
        # Heartbeat loop — replace with real event push when background tasks are added
        while True:
            await asyncio.sleep(15)
            yield {
                "event": "heartbeat",
                "data": json.dumps({"project_id": project_id}),
            }

    return EventSourceResponse(event_generator())

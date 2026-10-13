import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.trace import TraceCreate, TraceRead
from app.services.project_service import get_project
from app.services.trace_service import create_trace, list_traces

router = APIRouter(prefix="/projects", tags=["traces"])


@router.post("/{project_id}/traces", response_model=TraceRead, status_code=status.HTTP_201_CREATED)
def add_project_trace(project_id: str, payload: TraceCreate, db: Session = Depends(get_db)) -> TraceRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    trace = create_trace(db, project_id, payload.event, payload.stage, payload.message, payload.details)
    return TraceRead(
        id=trace.id,
        project_id=trace.project_id,
        event=trace.event,
        stage=trace.stage,
        message=trace.message,
        details=json.loads(trace.details) if trace.details else None,
        created_at=trace.created_at,
    )


@router.get("/{project_id}/traces", response_model=list[TraceRead])
def read_project_traces(project_id: str, db: Session = Depends(get_db)) -> list[TraceRead]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    traces = list_traces(db, project_id)
    return [
        TraceRead(
            id=trace.id,
            project_id=trace.project_id,
            event=trace.event,
            stage=trace.stage,
            message=trace.message,
            details=json.loads(trace.details) if trace.details else None,
            created_at=trace.created_at,
        )
        for trace in traces
    ]

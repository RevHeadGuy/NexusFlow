import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.trace import ProjectTrace


def list_traces(db: Session, project_id: str) -> list[ProjectTrace]:
    return db.scalars(
        select(ProjectTrace)
        .where(ProjectTrace.project_id == project_id)
        .order_by(ProjectTrace.created_at.desc())
    ).all()


def create_trace(db: Session, project_id: str, event: str, stage: str, message: str, details: dict | None = None) -> ProjectTrace:
    trace = ProjectTrace(
        project_id=project_id,
        event=event,
        stage=stage,
        message=message,
        details=json.dumps(details) if details is not None else None,
    )
    db.add(trace)
    db.commit()
    db.refresh(trace)
    return trace

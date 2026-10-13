from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.research_source import ResearchSource


def list_research_sources(db: Session, project_id: str) -> list[ResearchSource]:
    return db.scalars(
        select(ResearchSource)
        .where(ResearchSource.project_id == project_id)
        .order_by(ResearchSource.created_at.desc())
    ).all()


def create_research_source(db: Session, project_id: str, data: dict) -> ResearchSource:
    source = ResearchSource(project_id=project_id, **data)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def get_research_source(db: Session, project_id: str, source_id: str) -> ResearchSource | None:
    source = db.get(ResearchSource, source_id)
    return source if source and source.project_id == project_id else None


def update_research_source_review(db: Session, source: ResearchSource, reviewed: bool) -> ResearchSource:
    source.reviewed = reviewed
    db.commit()
    db.refresh(source)
    return source


def delete_research_source(db: Session, source: ResearchSource) -> None:
    db.delete(source)
    db.commit()

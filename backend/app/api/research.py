from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.artifact import ArtifactRead
from app.schemas.research import ResearchSourceCreate, ResearchSourceRead, ResearchSourceReview
from app.services.project_service import get_project
from app.services.stage_service import refresh_research_plan
from app.services.research_service import (
    create_research_source,
    delete_research_source,
    get_research_source,
    list_research_sources,
    update_research_source_review,
)

router = APIRouter(prefix="/projects", tags=["research"])


def _read(source) -> ResearchSourceRead:
    return ResearchSourceRead(
        id=source.id,
        project_id=source.project_id,
        title=source.title,
        url=source.url,
        finding=source.finding,
        notes=source.notes,
        added_by=source.added_by,
        reviewed=source.reviewed,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


@router.get("/{project_id}/research-sources", response_model=list[ResearchSourceRead])
def read_sources(project_id: str, db: Session = Depends(get_db)) -> list[ResearchSourceRead]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return [_read(source) for source in list_research_sources(db, project_id)]


@router.post(
    "/{project_id}/research-sources",
    response_model=ResearchSourceRead,
    status_code=status.HTTP_201_CREATED,
)
def add_source(
    project_id: str,
    payload: ResearchSourceCreate,
    db: Session = Depends(get_db),
) -> ResearchSourceRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    source = create_research_source(
        db,
        project_id,
        {
            "title": payload.title.strip(),
            "url": str(payload.url),
            "finding": payload.finding.strip(),
            "notes": payload.notes.strip() if payload.notes else None,
            "added_by": payload.added_by.strip(),
        },
    )
    return _read(source)


@router.patch("/{project_id}/research-sources/{source_id}", response_model=ResearchSourceRead)
def review_source(
    project_id: str,
    source_id: str,
    payload: ResearchSourceReview,
    db: Session = Depends(get_db),
) -> ResearchSourceRead:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    source = get_research_source(db, project_id, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return _read(update_research_source_review(db, source, payload.reviewed))


@router.delete("/{project_id}/research-sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_source(project_id: str, source_id: str, db: Session = Depends(get_db)) -> None:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    source = get_research_source(db, project_id, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    delete_research_source(db, source)


@router.post("/{project_id}/research-plan/refresh", response_model=ArtifactRead)
def update_research_plan(project_id: str, db: Session = Depends(get_db)) -> ArtifactRead:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    artifact = refresh_research_plan(db, project)
    return ArtifactRead(
        id=artifact.id,
        project_id=artifact.project_id,
        name=artifact.name,
        type=artifact.type,
        content=artifact.content,
        current_version=artifact.current_version,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )

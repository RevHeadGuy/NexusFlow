from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def list_projects(db: Session) -> list[Project]:
    return db.scalars(select(Project).order_by(Project.created_at.desc())).all()


def get_project(db: Session, project_id: str) -> Project | None:
    return db.get(Project, project_id)


def create_project(db: Session, payload: ProjectCreate) -> Project:
    project = Project(
        name=payload.name,
        description=payload.description,
        idea=payload.idea,
        status="draft",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project_id: str, payload: ProjectUpdate) -> Project | None:
    project = get_project(db, project_id)
    if project is None:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: str) -> bool:
    project = get_project(db, project_id)
    if project is None:
        return False

    db.delete(project)
    db.commit()
    return True

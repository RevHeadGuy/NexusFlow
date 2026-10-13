from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project_brief import ProjectBrief
from app.schemas.project_brief import ProjectBriefBase


def get_project_brief(db: Session, project_id: str) -> ProjectBrief | None:
    return db.scalar(select(ProjectBrief).where(ProjectBrief.project_id == project_id))


def save_project_brief(db: Session, project_id: str, payload: ProjectBriefBase) -> ProjectBrief:
    brief = get_project_brief(db, project_id)

    if brief is None:
        brief = ProjectBrief(project_id=project_id)

    brief.problem_statement = payload.problem_statement
    brief.target_users = payload.target_users
    brief.goals = payload.goals
    brief.constraints = payload.constraints
    brief.success_criteria = payload.success_criteria
    brief.clarifying_questions = payload.clarifying_questions

    db.add(brief)
    db.commit()
    db.refresh(brief)
    return brief

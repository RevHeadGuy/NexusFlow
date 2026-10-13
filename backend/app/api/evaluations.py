from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.evaluation import EvaluationReport
from app.services.evaluation_service import generate_consistency_check, generate_devils_advocate, list_reports, serialize_report
from app.services.project_service import get_project

router = APIRouter(prefix="/projects", tags=["evaluations"])


@router.post("/{project_id}/evaluations/consistency-check")
def run_consistency_check(project_id: str, db: Session = Depends(get_db)) -> dict:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    report = generate_consistency_check(db, project_id, project.idea, project.description)
    return serialize_report(db, report)


@router.post("/{project_id}/evaluations/devils-advocate")
def run_devils_advocate(project_id: str, db: Session = Depends(get_db)) -> dict:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    report = generate_devils_advocate(db, project_id, project.idea, project.description)
    return serialize_report(db, report)


@router.get("/{project_id}/evaluations")
def read_evaluations(project_id: str, db: Session = Depends(get_db)) -> list[dict]:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return [serialize_report(db, report) for report in list_reports(db, project_id)]


@router.get("/{project_id}/evaluations/{evaluation_id}")
def read_evaluation(project_id: str, evaluation_id: str, db: Session = Depends(get_db)) -> dict:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    report = db.get(EvaluationReport, evaluation_id)
    if report is None or report.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation report not found")

    return serialize_report(db, report)

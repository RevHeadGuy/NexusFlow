from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import EvaluationFinding, EvaluationReport


def list_reports(db: Session, project_id: str) -> list[EvaluationReport]:
    return db.scalars(
        select(EvaluationReport)
        .where(EvaluationReport.project_id == project_id)
        .order_by(EvaluationReport.created_at.desc())
    ).all()


def _findings_for_report(db: Session, report_id: str) -> list[dict]:
    rows = db.scalars(
        select(EvaluationFinding)
        .where(EvaluationFinding.report_id == report_id)
        .order_by(EvaluationFinding.created_at.asc())
    ).all()
    return [
        {
            "id": row.id,
            "category": row.category,
            "severity": row.severity,
            "title": row.title,
            "description": row.description,
            "evidence": row.evidence,
            "recommendation": row.recommendation,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


def serialize_report(db: Session, report: EvaluationReport) -> dict:
    return {
        "id": report.id,
        "project_id": report.project_id,
        "report_type": report.report_type,
        "status": report.status,
        "summary": report.summary,
        "findings": _findings_for_report(db, report.id),
        "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat(),
    }


def _add_finding(db: Session, report: EvaluationReport, category: str, severity: str, title: str, description: str, evidence: str, recommendation: str | None = None) -> None:
    db.add(
        EvaluationFinding(
            report_id=report.id,
            category=category,
            severity=severity,
            title=title,
            description=description,
            evidence=evidence,
            recommendation=recommendation,
        )
    )


def generate_consistency_check(db: Session, project_id: str, idea: str, description: str | None) -> EvaluationReport:
    report = EvaluationReport(project_id=project_id, report_type="consistency_check", summary="Consistency review of the project concept and scope.")
    db.add(report)
    db.commit()
    db.refresh(report)

    evidence_text = f"{idea} {description or ''}".strip()
    if len(evidence_text.split()) < 12:
        _add_finding(
            db,
            report,
            "scope",
            "warning",
            "Under-specified scope",
            "The current description is brief and may not communicate the target users, workflow, and constraints clearly enough.",
            evidence_text,
            "Add a concise problem statement, target users, and key constraints before enforcing the build plan.",
        )
    else:
        _add_finding(
            db,
            report,
            "scope",
            "info",
            "Scope is reasonably defined",
            "The project idea includes enough detail to support a structured review.",
            evidence_text[:220],
            "Keep the specification aligned as the design evolves.",
        )

    if any(keyword in idea.lower() for keyword in ["health", "medical", "patient", "clinical"]):
        _add_finding(
            db,
            report,
            "compliance",
            "warning",
            "Regulatory and privacy review likely required",
            "Healthcare-oriented workflows often require auditability, consent controls, and data handling review.",
            idea,
            "Confirm privacy requirements, access controls, and compliance ownership before implementation.",
        )

    db.commit()
    return report


def generate_devils_advocate(db: Session, project_id: str, idea: str, description: str | None) -> EvaluationReport:
    report = EvaluationReport(project_id=project_id, report_type="devils_advocate", summary="Adversarial review focused on risk and failure modes.")
    db.add(report)
    db.commit()
    db.refresh(report)

    evidence_text = f"{idea} {description or ''}".strip()
    _add_finding(
        db,
        report,
        "adoption",
        "warning",
        "Adoption risk is not yet proven",
        "The concept may depend on cross-functional buy-in, which can slow rollout if the workflow is not clearly designed for day-to-day operations.",
        evidence_text[:220],
        "Validate the user journey, team ownership, and rollout path with stakeholders before scaling.",
    )
    _add_finding(
        db,
        report,
        "technical",
        "critical",
        "Operational complexity may be underestimated",
        "A broad workflow platform often hides integration, permissions, and audit requirements behind a simple concept.",
        evidence_text[:220],
        "Break the scope into staged milestones and define integration constraints explicitly.",
    )

    db.commit()
    return report

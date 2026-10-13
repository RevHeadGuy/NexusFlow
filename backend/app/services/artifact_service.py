import io
import json
import re
import zipfile
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.artifact import ArtifactVersion, ProjectArtifact
from app.models.artifact_comment import ArtifactReviewComment
from app.models.project import Project
from app.models.project_brief import ProjectBrief
from app.models.research_source import ResearchSource
from app.models.workflow import WorkflowDecision, WorkflowPlan, WorkflowRun


def get_artifact(db: Session, artifact_id: str) -> ProjectArtifact | None:
    return db.get(ProjectArtifact, artifact_id)


def list_artifacts(db: Session, project_id: str) -> list[ProjectArtifact]:
    return db.scalars(select(ProjectArtifact).where(ProjectArtifact.project_id == project_id).order_by(ProjectArtifact.updated_at.desc())).all()


def get_artifact_for_project(db: Session, project_id: str, artifact_id: str) -> ProjectArtifact | None:
    artifact = db.get(ProjectArtifact, artifact_id)
    if artifact is None or artifact.project_id != project_id:
        return None
    return artifact


def get_versions(db: Session, artifact_id: str) -> list[ArtifactVersion]:
    return db.scalars(
        select(ArtifactVersion)
        .where(ArtifactVersion.artifact_id == artifact_id)
        .order_by(ArtifactVersion.version.asc())
    ).all()


def create_artifact(db: Session, project_id: str, name: str, artifact_type: str, content: str) -> ProjectArtifact:
    artifact = ProjectArtifact(
        project_id=project_id,
        name=name,
        type=artifact_type,
        content=content,
        current_version=1,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    version = ArtifactVersion(
        artifact_id=artifact.id,
        project_id=project_id,
        version=1,
        content=content,
        summary="Initial version",
    )
    db.add(version)
    db.commit()
    db.refresh(artifact)
    return artifact


def create_artifact_version(db: Session, artifact_id: str, content: str, summary: str | None = None) -> ArtifactVersion:
    artifact = db.get(ProjectArtifact, artifact_id)
    if artifact is None:
        raise ValueError("Artifact not found")

    next_version = artifact.current_version + 1
    artifact.current_version = next_version
    artifact.content = content
    artifact.updated_at

    version = ArtifactVersion(
        artifact_id=artifact.id,
        project_id=artifact.project_id,
        version=next_version,
        content=content,
        summary=summary,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    db.refresh(artifact)
    return version


def export_artifact_zip(db: Session, artifact_id: str) -> bytes:
    artifact = db.get(ProjectArtifact, artifact_id)
    if artifact is None:
        raise ValueError("Artifact not found")

    versions = get_versions(db, artifact_id)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        manifest = {
            "artifact_id": artifact.id,
            "project_id": artifact.project_id,
            "name": artifact.name,
            "type": artifact.type,
            "current_version": artifact.current_version,
            "versions": [
                {
                    "version": version.version,
                    "summary": version.summary,
                    "created_at": version.created_at.isoformat(),
                }
                for version in versions
            ],
        }
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))

        latest_content = artifact.content
        latest_extension = ".md" if artifact.type == "markdown" else f".{artifact.type}"
        archive.writestr(f"{artifact.name}{latest_extension}", latest_content)

        for version in versions:
            filename = f"{artifact.name}_v{version.version}.md" if artifact.type == "markdown" else f"{artifact.name}_v{version.version}.{artifact.type}"
            archive.writestr(filename, version.content)

    buffer.seek(0)
    return buffer.getvalue()


def export_project_package(db: Session, project_id: str) -> bytes:
    """Build a portable ZIP with project context, evidence, decisions, reviews, and artifact history."""
    project = db.get(Project, project_id)
    artifacts = list_artifacts(db, project_id)
    brief = db.scalar(select(ProjectBrief).where(ProjectBrief.project_id == project_id))
    workflow = db.scalar(select(WorkflowRun).where(WorkflowRun.project_id == project_id))
    plan = db.scalar(select(WorkflowPlan).where(WorkflowPlan.workflow_run_id == workflow.id)) if workflow else None
    decisions = db.scalars(
        select(WorkflowDecision).where(WorkflowDecision.project_id == project_id).order_by(WorkflowDecision.created_at.asc())
    ).all()
    sources = db.scalars(
        select(ResearchSource).where(ResearchSource.project_id == project_id).order_by(ResearchSource.created_at.asc())
    ).all()
    comments = db.scalars(
        select(ArtifactReviewComment).where(ArtifactReviewComment.project_id == project_id).order_by(ArtifactReviewComment.created_at.asc())
    ).all()

    def iso(value):
        return value.isoformat() if value else None

    project_data = None if project is None else {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "idea": project.idea,
        "status": project.status,
        "created_at": iso(project.created_at),
        "updated_at": iso(project.updated_at),
    }
    brief_data = None if brief is None else {
        "problem_statement": brief.problem_statement,
        "target_users": brief.target_users,
        "goals": brief.goals,
        "constraints": brief.constraints,
        "success_criteria": brief.success_criteria,
        "clarifying_questions": brief.clarifying_questions,
        "updated_at": iso(brief.updated_at),
    }
    decision_data = [
        {"stage": item.stage, "action": item.action, "notes": item.notes, "created_at": iso(item.created_at)}
        for item in decisions
    ]
    source_data = [
        {
            "title": item.title,
            "url": item.url,
            "finding": item.finding,
            "notes": item.notes,
            "added_by": item.added_by,
            "reviewed": item.reviewed,
            "created_at": iso(item.created_at),
        }
        for item in sources
    ]
    comment_data = [
        {
            "artifact_id": item.artifact_id,
            "artifact_name": next((artifact.name for artifact in artifacts if artifact.id == item.artifact_id), None),
            "version_number": item.version_number,
            "section_key": item.section_key,
            "reviewer_name": item.reviewer_name,
            "comment": item.comment,
            "suggested_edit": item.suggested_edit,
            "resolved": item.resolved,
            "created_at": iso(item.created_at),
            "resolved_at": iso(item.resolved_at),
        }
        for item in comments
    ]
    workflow_data = None if workflow is None else {
        "status": workflow.status,
        "current_stage": workflow.current_stage,
        "template_key": plan.template_key if plan else "full_product",
        "stage_plan": json.loads(plan.stage_keys) if plan else [],
        "decisions": decision_data,
    }

    summary_sections = []
    if project:
        summary_sections.extend([f"# {project.name}", f"## Project idea\n\n{project.idea}"])
        if project.description:
            summary_sections.insert(1, f"## Summary\n\n{project.description}")
    if brief_data:
        brief_sections = [f"## Problem statement\n\n{brief_data['problem_statement']}"]
        for label, key in [("Target users", "target_users"), ("Goals", "goals"), ("Constraints", "constraints"), ("Success criteria", "success_criteria"), ("Open questions", "clarifying_questions")]:
            values = brief_data[key]
            brief_sections.append(f"### {label}\n\n" + ("\n".join(f"- {value}" for value in values) or "- None recorded"))
        summary_sections.extend(brief_sections)
    if workflow_data:
        summary_sections.append(
            "## Workflow\n\n"
            f"- Status: {workflow_data['status']}\n"
            f"- Current stage: {workflow_data['current_stage']}\n"
            f"- Template: {workflow_data['template_key']}\n"
            f"- Stage plan: {', '.join(workflow_data['stage_plan'])}"
        )
        summary_sections.append("## Decision history\n\n" + ("\n".join(
            f"- **{item['stage']} — {item['action']}** ({item['created_at']})" + (f": {item['notes']}" if item["notes"] else "")
            for item in decision_data
        ) or "No decisions recorded."))
    summary_sections.append("## Research sources\n\n" + ("\n".join(
        f"- [{item['title']}]({item['url']}) — {item['finding']} (reviewed: {item['reviewed']})"
        for item in source_data
    ) or "No sources recorded."))
    unresolved_comments = [item for item in comment_data if not item["resolved"]]
    summary_sections.append("## Unresolved review feedback\n\n" + ("\n".join(
        f"- **{item['artifact_name'] or 'Artifact'} v{item['version_number']} / {item['section_key']}** — {item['comment']}"
        for item in unresolved_comments
    ) or "No unresolved feedback."))

    buffer = io.BytesIO()
    manifest = {
        "project_id": project_id,
        "project_name": project.name if project else None,
        "artifact_count": len(artifacts),
        "decision_count": len(decisions),
        "research_source_count": len(sources),
        "unresolved_review_comment_count": len(unresolved_comments),
        "artifacts": [],
    }
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.md", "\n\n".join(summary_sections) + "\n")
        archive.writestr("project/project.json", json.dumps(project_data, indent=2))
        archive.writestr("project/brief.json", json.dumps(brief_data, indent=2))
        archive.writestr("workflow/workflow.json", json.dumps(workflow_data, indent=2))
        archive.writestr("workflow/decisions.json", json.dumps(decision_data, indent=2))
        archive.writestr("research/sources.json", json.dumps(source_data, indent=2))
        archive.writestr("reviews/comments.json", json.dumps(comment_data, indent=2))
        for artifact in sorted(artifacts, key=lambda item: (item.name.lower(), item.id)):
            safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", artifact.name).strip("._") or "artifact"
            version_history = get_versions(db, artifact.id)
            extension = ".md" if artifact.type == "markdown" else f".{artifact.type}"
            archive.writestr(f"artifacts/{safe_name}-{artifact.id[:8]}{extension}", artifact.content)
            for version in version_history:
                archive.writestr(f"artifact-versions/{safe_name}-{artifact.id[:8]}/v{version.version}{extension}", version.content)
            manifest["artifacts"].append({
                "id": artifact.id,
                "name": artifact.name,
                "type": artifact.type,
                "version": artifact.current_version,
                "updated_at": artifact.updated_at.isoformat(),
                "version_count": len(version_history),
            })
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
    buffer.seek(0)
    return buffer.getvalue()

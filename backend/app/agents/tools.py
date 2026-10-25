"""Project-context tools shared by agents and the MCP server.

These are the single source of truth for read-only project context. The MCP
server (``app.mcp_server``) exposes them over HTTP for external clients, and
agents call them in-process through :class:`ProjectToolbox` to ground their
output in real project data (brief, workflow state, prior artifacts).

Keeping one implementation means an agent reading an artifact and an MCP client
reading the same artifact go through identical logic, and there is no network
hop or per-user-auth limitation for the in-process agent path.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.artifact import ProjectArtifact
from app.models.project import Project
from app.models.project_brief import ProjectBrief
from app.services.workflow_service import get_workflow_by_project, get_workflow_decisions


def project_context(db: Session, project_id: str) -> dict:
    """Return a project's idea, brief, workflow stage, and recorded decisions."""
    project = db.get(Project, project_id)
    if project is None:
        return {"error": "Project not found"}
    brief = db.scalar(select(ProjectBrief).where(ProjectBrief.project_id == project_id))
    workflow = get_workflow_by_project(db, project_id)
    decisions = get_workflow_decisions(db, workflow.id) if workflow else []
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "idea": project.idea,
        },
        "brief": None if brief is None else {
            "problem_statement": brief.problem_statement,
            "target_users": brief.target_users,
            "goals": brief.goals,
            "constraints": brief.constraints,
            "success_criteria": brief.success_criteria,
            "clarifying_questions": brief.clarifying_questions,
        },
        "workflow": None if workflow is None else {
            "current_stage": workflow.current_stage,
            "status": workflow.status,
            "decisions": [
                {"stage": item.stage, "action": item.action, "notes": item.notes}
                for item in decisions
            ],
        },
    }


def list_artifacts(db: Session, project_id: str) -> list[dict]:
    """List artifact names, types, versions, and update times for one project."""
    if db.get(Project, project_id) is None:
        return [{"error": "Project not found"}]
    artifacts = db.scalars(
        select(ProjectArtifact)
        .where(ProjectArtifact.project_id == project_id)
        .order_by(ProjectArtifact.updated_at.desc())
    ).all()
    return [
        {
            "id": artifact.id,
            "name": artifact.name,
            "type": artifact.type,
            "version": artifact.current_version,
            "updated_at": artifact.updated_at.isoformat(),
        }
        for artifact in artifacts
    ]


def read_artifact(db: Session, project_id: str, artifact_id: str) -> dict:
    """Read an artifact's latest content after verifying it belongs to the project."""
    if db.get(Project, project_id) is None:
        return {"error": "Project not found"}
    artifact = db.scalar(
        select(ProjectArtifact).where(
            ProjectArtifact.id == artifact_id,
            ProjectArtifact.project_id == project_id,
        )
    )
    if artifact is None:
        return {"error": "Artifact not found in this project"}
    return {
        "id": artifact.id,
        "name": artifact.name,
        "type": artifact.type,
        "version": artifact.current_version,
        "content": artifact.content,
    }


def read_artifact_by_name(db: Session, project_id: str, name: str) -> dict:
    """Read the latest content of a project artifact by its name (case-insensitive)."""
    if db.get(Project, project_id) is None:
        return {"error": "Project not found"}
    artifacts = db.scalars(
        select(ProjectArtifact).where(ProjectArtifact.project_id == project_id)
    ).all()
    match = next((a for a in artifacts if a.name.lower() == name.lower()), None)
    if match is None:
        return {"error": f"Artifact named '{name}' not found in this project"}
    return {
        "id": match.id,
        "name": match.name,
        "type": match.type,
        "version": match.current_version,
        "content": match.content,
    }


class ProjectToolbox:
    """A thin, project-scoped wrapper agents use to read project context.

    Bound to one database session and project, so an agent can call tools without
    threading ids through every call. Every method is read-only.
    """

    def __init__(self, db: Session, project_id: str) -> None:
        self._db = db
        self._project_id = project_id

    def get_context(self) -> dict:
        return project_context(self._db, self._project_id)

    def list_artifacts(self) -> list[dict]:
        return list_artifacts(self._db, self._project_id)

    def read_artifact_by_name(self, name: str) -> dict:
        return read_artifact_by_name(self._db, self._project_id, name)

    def gather_prior_artifacts(self, names: list[str]) -> dict[str, str]:
        """Return a ``{name: content}`` map for the requested artifacts that exist.

        Used by later-stage agents to ground their output in earlier deliverables
        (e.g. the architecture agent reading the PRD and feasibility artifacts).
        """
        gathered: dict[str, str] = {}
        for name in names:
            result = self.read_artifact_by_name(name)
            if "content" in result and result["content"]:
                gathered[result["name"]] = result["content"]
        return gathered

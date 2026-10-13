"""Read-only NexusFlow MCP server for project-scoped context and artifacts.

Run from ``backend`` with ``python -m app.mcp_server``. It binds to loopback
so the development tool endpoint is not exposed to the local network.
"""

from mcp.server.mcpserver import MCPServer
from sqlalchemy import select

from app.database import SessionLocal
from app.models.artifact import ProjectArtifact
from app.models.project import Project
from app.models.project_brief import ProjectBrief
from app.services.workflow_service import get_workflow_by_project, get_workflow_decisions

mcp = MCPServer(
    "NexusFlow",
    instructions=(
        "Read-only tools for retrieving project-scoped NexusFlow context and artifacts. "
        "These tools do not create, edit, approve, or delete project data."
    ),
)


@mcp.tool()
def get_project_context(project_id: str) -> dict:
    """Read a project's idea, brief, workflow stage, and recorded decisions."""
    with SessionLocal() as db:
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


@mcp.tool()
def list_project_artifacts(project_id: str) -> list[dict]:
    """List artifact names, types, versions, and update times for one project."""
    with SessionLocal() as db:
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


@mcp.tool()
def read_project_artifact(project_id: str, artifact_id: str) -> dict:
    """Read an artifact's latest content after verifying it belongs to the project."""
    with SessionLocal() as db:
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


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        json_response=True,
        stateless_http=True,
    )

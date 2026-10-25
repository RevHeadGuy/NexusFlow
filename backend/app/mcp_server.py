"""Read-only NexusFlow MCP server for project-scoped context and artifacts.

Run from ``backend`` with ``python -m app.mcp_server``. It binds to loopback
so the development tool endpoint is not exposed to the local network.
"""

from mcp.server.mcpserver import MCPServer
from sqlalchemy import func, select

from app.agents import tools as project_tools
from app.database import SessionLocal
from app.models.auth import ProjectMembership, User
from app.models.project import Project

mcp = MCPServer(
    "NexusFlow",
    instructions=(
        "Read-only tools for retrieving project-scoped NexusFlow context and artifacts. "
        "These tools do not create, edit, approve, or delete project data."
    ),
)


def _is_single_member_project(db, project_id: str) -> bool:
    """MCP has no per-user identity yet, so disable it for collaborative accounts."""
    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    member_count = db.scalar(
        select(func.count()).select_from(ProjectMembership).where(ProjectMembership.project_id == project_id)
    )
    return user_count <= 1 and member_count == 1


_MULTI_MEMBER_ERROR = (
    "MCP access is disabled when multiple accounts exist because MCP has no "
    "per-user authentication yet."
)


@mcp.tool()
def get_project_context(project_id: str) -> dict:
    """Read a project's idea, brief, workflow stage, and recorded decisions."""
    with SessionLocal() as db:
        if db.get(Project, project_id) is None:
            return {"error": "Project not found"}
        if not _is_single_member_project(db, project_id):
            return {"error": _MULTI_MEMBER_ERROR}
        return project_tools.project_context(db, project_id)


@mcp.tool()
def list_project_artifacts(project_id: str) -> list[dict]:
    """List artifact names, types, versions, and update times for one project."""
    with SessionLocal() as db:
        if db.get(Project, project_id) is None:
            return [{"error": "Project not found"}]
        if not _is_single_member_project(db, project_id):
            return [{"error": _MULTI_MEMBER_ERROR}]
        return project_tools.list_artifacts(db, project_id)


@mcp.tool()
def read_project_artifact(project_id: str, artifact_id: str) -> dict:
    """Read an artifact's latest content after verifying it belongs to the project."""
    with SessionLocal() as db:
        if db.get(Project, project_id) is None:
            return {"error": "Project not found"}
        if not _is_single_member_project(db, project_id):
            return {"error": _MULTI_MEMBER_ERROR}
        return project_tools.read_artifact(db, project_id, artifact_id)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        json_response=True,
        stateless_http=True,
    )

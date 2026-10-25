from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import SessionLocal
from app.models.auth import ProjectMembership, User
from app.models.mlops import AgentRun
from app.models.project import Project
from app.services.auth_service import decode_access_token


PUBLIC_PATHS = {"/health", "/auth/register", "/auth/login", "/docs", "/redoc", "/openapi.json"}
ROLE_RANK = {"viewer": 1, "reviewer": 2, "editor": 3, "owner": 4}


class IdentityAndProjectAccessMiddleware(BaseHTTPMiddleware):
    """Authenticate API calls and enforce project membership before route execution."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"
        if request.method == "OPTIONS" or path in PUBLIC_PATHS or path.startswith("/_next/"):
            return await call_next(request)

        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        user_id = decode_access_token(token) if scheme.lower() == "bearer" and token else None
        if not user_id:
            return JSONResponse({"detail": "Sign in to access NexusFlow."}, status_code=401)

        db = SessionLocal()
        try:
            user = db.get(User, user_id)
            if user is None:
                return JSONResponse({"detail": "Account no longer exists."}, status_code=401)

            project_id = self._project_id(path)
            if project_id:
                project = db.get(Project, project_id)
                if project is None:
                    return JSONResponse({"detail": "Project not found."}, status_code=404)
                membership = db.query(ProjectMembership).filter_by(project_id=project_id, user_id=user.id).first()
                if membership is None:
                    return JSONResponse({"detail": "You do not have access to this project."}, status_code=404)
                denied = self._role_denial(path, request.method, membership.role)
                if denied:
                    return JSONResponse({"detail": denied}, status_code=403)

            if path.startswith("/mlops/runs/"):
                run_id = path.split("/")[3] if len(path.split("/")) > 3 else ""
                run = db.get(AgentRun, run_id)
                if run is None:
                    return JSONResponse({"detail": "Run not found."}, status_code=404)
                membership = db.query(ProjectMembership).filter_by(project_id=run.project_id, user_id=user.id).first()
                if membership is None:
                    return JSONResponse({"detail": "You do not have access to this run."}, status_code=404)

            if path.startswith("/dashboard/events/"):
                project_id = path.rsplit("/", 1)[-1]
                membership = db.query(ProjectMembership).filter_by(project_id=project_id, user_id=user.id).first()
                if membership is None:
                    return JSONResponse({"detail": "You do not have access to this project."}, status_code=404)

            request.state.user = user
            return await call_next(request)
        finally:
            db.close()

    @staticmethod
    def _project_id(path: str) -> str | None:
        parts = path.split("/")
        if len(parts) >= 3 and parts[1] == "projects" and parts[2] not in {"", "new"}:
            return parts[2]
        return None

    @staticmethod
    def _role_denial(path: str, method: str, role: str) -> str | None:
        if "/invitations" in path or ("/members" in path and method != "GET"):
            required = "owner"
        elif method == "DELETE" and path.count("/") == 2:
            required = "owner"
        elif method in {"POST", "PUT", "PATCH", "DELETE"}:
            review_action = any(part in path for part in ("/decision", "/review", "/feedback", "/comments", "/override"))
            required = "reviewer" if review_action else "editor"
        else:
            required = "viewer"
        if ROLE_RANK.get(role, 0) < ROLE_RANK[required]:
            return f"This action requires the {required} project role or higher."
        return None

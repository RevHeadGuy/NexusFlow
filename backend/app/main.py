from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.artifacts import router as artifact_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.evaluations import router as evaluation_router
from app.api.guardrails import router as guardrail_router
from app.api.hitl import global_router as review_queue_router
from app.api.hitl import project_router as hitl_router
from app.api.mlops import router as mlops_router
from app.api.members import router as members_router
from app.api.projects import router as project_router
from app.api.research import router as research_router
from app.api.review_comments import router as review_comments_router
from app.api.traces import router as trace_router
from app.api.workflow import router as workflow_router
from app.api.workflow import review_router as workflow_review_queue_router
from app.config import get_settings
from app.database import init_db
from app.security import IdentityAndProjectAccessMiddleware

# Model imports ensure SQLAlchemy registers all tables before init_db() runs
from app.models.agent_message import AgentMessage  # noqa: F401
from app.models.artifact import ArtifactVersion, ProjectArtifact  # noqa: F401
from app.models.auth import ProjectInvitation, ProjectMembership, User, WorkflowDecisionActor  # noqa: F401
from app.models.artifact_comment import ArtifactReviewComment  # noqa: F401
from app.models.evaluation import EvaluationFinding, EvaluationReport  # noqa: F401
from app.models.guardrail import GuardrailViolationRecord  # noqa: F401
from app.models.hitl import ArtifactFeedback, HumanCheckpoint  # noqa: F401
from app.models.mlops import AgentRun, EvaluationScore, PromptVersion  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.project_brief import ProjectBrief  # noqa: F401
from app.models.research_source import ResearchSource  # noqa: F401
from app.models.trace import ProjectTrace  # noqa: F401
from app.models.workflow import WorkflowDecision, WorkflowPlan, WorkflowRun  # noqa: F401

settings = get_settings()
init_db()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="NexusFlow API",
    description="Local-first API for human-reviewed project planning workflows",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(IdentityAndProjectAccessMiddleware)

app.include_router(auth_router)

# Core project routes
app.include_router(project_router)
app.include_router(members_router)
app.include_router(workflow_router)
app.include_router(workflow_review_queue_router)
app.include_router(artifact_router)
app.include_router(research_router)
app.include_router(review_comments_router)
app.include_router(evaluation_router)
app.include_router(trace_router)

# Guardrails
app.include_router(guardrail_router)

# Human-in-the-Loop
app.include_router(hitl_router)
app.include_router(review_queue_router)

# MLOps
app.include_router(mlops_router)

# Dashboard + SSE
app.include_router(dashboard_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "NexusFlow",
        "version": "0.2.0",
    }

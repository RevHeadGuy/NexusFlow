"""Model registry.

Importing this package registers every ORM model on ``Base.metadata``. Both the
app startup path and Alembic autogenerate rely on that, so keep this list
complete whenever a new model module is added.
"""

from app.models.agent_message import AgentMessage
from app.models.artifact import ArtifactVersion, ProjectArtifact
from app.models.artifact_comment import ArtifactReviewComment
from app.models.auth import ProjectInvitation, ProjectMembership, User, WorkflowDecisionActor
from app.models.evaluation import EvaluationFinding, EvaluationReport
from app.models.guardrail import GuardrailViolationRecord
from app.models.hitl import ArtifactFeedback, HumanCheckpoint
from app.models.mlops import AgentRun, EvaluationScore, PromptVersion
from app.models.project import Project
from app.models.project_brief import ProjectBrief
from app.models.research_source import ResearchSource
from app.models.trace import ProjectTrace
from app.models.workflow import WorkflowDecision, WorkflowPlan, WorkflowRun

__all__ = [
    "AgentMessage",
    "ArtifactVersion",
    "ProjectArtifact",
    "ArtifactReviewComment",
    "ProjectInvitation",
    "ProjectMembership",
    "User",
    "WorkflowDecisionActor",
    "EvaluationFinding",
    "EvaluationReport",
    "GuardrailViolationRecord",
    "ArtifactFeedback",
    "HumanCheckpoint",
    "AgentRun",
    "EvaluationScore",
    "PromptVersion",
    "Project",
    "ProjectBrief",
    "ResearchSource",
    "ProjectTrace",
    "WorkflowDecision",
    "WorkflowPlan",
    "WorkflowRun",
]

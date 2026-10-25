from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent


class IdeaBriefOutput(BaseModel):
    problem_statement: str = Field(..., min_length=10)
    target_users: list[str] = Field(..., min_length=1)
    goals: list[str] = Field(..., min_length=1)
    constraints: list[str] = Field(..., min_length=1)
    success_criteria: list[str] = Field(..., min_length=1)
    clarifying_questions: list[str] = Field(default_factory=list)


IDEA_ANALYST_PROMPT = """
You are the Idea Analyst for NexusFlow. Turn a raw product idea into a structured brief.

Requirements:
- Disambiguate the problem, target users, goals, constraints, and success criteria.
- Ask only one or two high-value clarifying questions when necessary.
- Prefer concrete language over vague market hype.
- Do not invent facts not present in the user's idea; explicitly label missing information as assumptions.
- Output valid structured data with clear lists.
"""


class IdeaAnalystAgent(BaseAgent):
    """Turns a raw product idea into a structured, schema-validated brief."""

    agent_name = "idea_analyst"
    output_schema = IdeaBriefOutput
    default_prompt = IDEA_ANALYST_PROMPT
    max_output_tokens = 1200
    mock_sample = {
        "problem_statement": (
            "The project needs a concrete problem statement derived from the user idea."
        ),
        "target_users": ["target users"],
        "goals": ["define a clear goal"],
        "constraints": ["document assumptions"],
        "success_criteria": ["establish measurable outcomes"],
        "clarifying_questions": ["What is the primary user problem you want to solve?"],
    }


def analyze_idea(idea: str) -> tuple[dict[str, object], dict[str, object] | None]:
    """Analyze a raw idea and return ``(brief_dict, token_usage_or_None)``.

    Behavior and return shape are unchanged from the original implementation;
    provider selection now lives in :mod:`app.agents.providers` and the call flow
    in :class:`app.agents.base.BaseAgent`.
    """
    if not idea or not idea.strip():
        raise ValueError("Idea text is required for analysis.")

    agent = IdeaAnalystAgent()
    result = agent.run(idea)
    return result.output, result.usage

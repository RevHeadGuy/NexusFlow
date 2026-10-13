from __future__ import annotations

import json

import httpx
from pydantic import BaseModel, Field
from strands import Agent
from strands.models import BedrockModel

from app.config import get_settings


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


def _build_model() -> BedrockModel:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider != "bedrock":
        raise RuntimeError(
            f"Unsupported LLM provider '{settings.llm_provider}'. "
            "Phase 2 currently supports the Bedrock provider configuration."
        )

    aws_key_id = settings.aws_access_key_id or None
    aws_secret = settings.aws_secret_access_key or None
    if not aws_key_id or not aws_secret:
        raise RuntimeError(
            "Bedrock model configuration is missing AWS credentials. "
            "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY or use a mocked provider in tests."
        )

    return BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        api_key=settings.llm_api_key,
    )


def analyze_idea(idea: str) -> tuple[dict[str, object], dict[str, object] | None]:
    settings = get_settings()
    if not idea or not idea.strip():
        raise ValueError("Idea text is required for analysis.")

    if settings.llm_provider.lower() == "mock":
        return {
            "problem_statement": "The project needs a concrete problem statement derived from the user idea.",
            "target_users": ["target users"],
            "goals": ["define a clear goal"],
            "constraints": ["document assumptions"],
            "success_criteria": ["establish measurable outcomes"],
            "clarifying_questions": ["What is the primary user problem you want to solve?"],
        }, None

    if settings.llm_provider.lower() == "groq":
        if not settings.groq_api_key:
            raise RuntimeError("Groq is selected but GROQ_API_KEY is missing from backend/.env.")
        try:
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": [
                        {"role": "system", "content": IDEA_ANALYST_PROMPT},
                        {"role": "user", "content": idea},
                    ],
                    "response_format": {"type": "json_object"},
                    "max_completion_tokens": 1200,
                    "temperature": 0.2,
                },
                timeout=settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            brief = IdeaBriefOutput.model_validate(json.loads(content))
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Groq request failed with HTTP {exc.response.status_code}.") from exc
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Groq returned an invalid or unavailable analysis response.") from exc
        usage = body.get("usage") or {}
        return brief.model_dump(), {
            "provider": "groq",
            "model": body.get("model", settings.groq_model),
            "input_tokens": usage.get("prompt_tokens"),
            "output_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }

    agent = Agent(model=_build_model(), system_prompt=IDEA_ANALYST_PROMPT)
    brief = agent.structured_output(IdeaBriefOutput, prompt=idea)
    return brief.model_dump(), None

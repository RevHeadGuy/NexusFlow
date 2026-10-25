"""Reusable base class for NexusFlow model-backed agents.

``BaseAgent`` captures the pattern that previously lived only in the idea-analysis
endpoint: resolve the active prompt, call the configured LLM provider, and return
a validated structured output with token usage. Guardrail execution and run
tracking stay in the API/orchestration layer so this class has no database or
HTTP-framework dependencies and is trivial to unit test.

Subclasses declare three things: an ``agent_name`` (which must match the keys in
the guardrail/schema registries), an ``output_schema`` (a Pydantic model), and a
``default_prompt`` (used when no active ``PromptVersion`` is registered).
"""
from __future__ import annotations

from typing import Type

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.providers import LLMProvider, ProviderResult, get_provider
from app.config import Settings, get_settings
from app.services.mlops_service import get_active_prompt


class BaseAgent:
    """Base class every model-backed agent extends.

    Attributes
    ----------
    agent_name:
        Stable identifier used by guardrails, the prompt registry, and AgentRun
        records. Must be set by subclasses.
    output_schema:
        Pydantic model the provider output is validated against.
    default_prompt:
        System prompt used when the prompt registry has no active version.
    max_output_tokens / temperature:
        Generation controls passed to the provider.
    """

    agent_name: str = ""
    output_schema: Type[BaseModel]
    default_prompt: str = ""
    max_output_tokens: int = 1200
    temperature: float = 0.2
    # Optional guardrail-safe payload returned by the mock provider for this agent.
    mock_sample: dict[str, object] | None = None

    def __init__(
        self,
        *,
        provider: LLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        if not self.agent_name:
            raise ValueError(f"{type(self).__name__} must define a non-empty 'agent_name'.")
        if not getattr(self, "output_schema", None):
            raise ValueError(f"{type(self).__name__} must define an 'output_schema'.")
        self._settings = settings or get_settings()
        self._provider = provider or get_provider(self._settings, mock_sample=self.mock_sample)

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    def resolve_prompt(self, db: Session | None = None) -> str:
        """Return the active prompt from the registry, falling back to the default.

        When a database session is supplied and an active ``PromptVersion`` exists
        for this agent, its content is used. Otherwise the subclass default prompt
        is returned. This finally wires the long-dormant prompt registry into the
        agents that use it.
        """
        if db is not None:
            active = get_active_prompt(db, self.agent_name)
            if active is not None and active.content.strip():
                return active.content
        if not self.default_prompt.strip():
            raise ValueError(
                f"Agent '{self.agent_name}' has no active prompt version and no default_prompt."
            )
        return self.default_prompt

    def run(self, user_prompt: str, *, db: Session | None = None) -> ProviderResult:
        """Generate structured output for ``user_prompt`` using the active prompt.

        This performs the provider call only. Callers remain responsible for
        guardrail enforcement and AgentRun tracking so the agent stays decoupled
        from the request lifecycle.
        """
        if not user_prompt or not user_prompt.strip():
            raise ValueError("A non-empty user prompt is required.")
        system_prompt = self.resolve_prompt(db)
        return self._provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=self.output_schema,
            max_output_tokens=self.max_output_tokens,
            temperature=self.temperature,
        )

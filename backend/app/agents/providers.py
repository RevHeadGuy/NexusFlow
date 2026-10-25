"""LLM provider abstraction for NexusFlow agents.

This module extracts the provider-selection logic that previously lived inline
in ``idea_analyst.analyze_idea`` into a small, reusable interface. Every agent
in the system talks to a provider through :class:`LLMProvider`, so adding a new
agent no longer means copying an if/elif ladder.

Providers are intentionally thin: they take a system prompt, a user prompt, and
a Pydantic output schema, and return a validated model instance plus optional
token-usage accounting. Guardrails, run tracking, and tracing live one layer up
in :mod:`app.agents.base`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol, Type, TypeVar

import httpx
from pydantic import BaseModel

from app.config import Settings, get_settings

OutputT = TypeVar("OutputT", bound=BaseModel)


@dataclass
class ProviderResult:
    """Structured output from a provider call plus optional usage accounting."""

    output: dict[str, object]
    usage: dict[str, object] | None = None


class LLMProvider(Protocol):
    """Common interface implemented by every provider.

    Implementations validate the raw model output against ``schema`` and return a
    :class:`ProviderResult`. They should raise ``RuntimeError`` with an actionable
    message on configuration or transport failures so callers can surface a clean
    error instead of a traceback.
    """

    name: str

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: Type[OutputT],
        max_output_tokens: int = 1200,
        temperature: float = 0.2,
    ) -> ProviderResult:
        ...


class MockProvider:
    """Deterministic provider used for local development and CI.

    It never makes a network call. The output is a minimal, schema-shaped sample
    so the full agent pipeline (guardrails, run tracking, persistence) can run
    without cloud credentials. It is not meant to produce useful content.
    """

    name = "mock"

    def __init__(self, sample: dict[str, object] | None = None) -> None:
        # An agent may supply a tailored sample so the mock output passes the
        # agent's own guardrails (scope/length). Falls back to a generic payload.
        self._sample = sample

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: Type[OutputT],
        max_output_tokens: int = 1200,
        temperature: float = 0.2,
    ) -> ProviderResult:
        sample = self._sample if self._sample is not None else _mock_sample_for(schema)
        validated = schema.model_validate(sample)
        return ProviderResult(output=validated.model_dump(), usage=None)


class GroqProvider:
    """Calls Groq's OpenAI-compatible chat completions endpoint.

    Requires ``GROQ_API_KEY`` in the backend environment. The model is asked for a
    JSON object, which is validated against the agent's output schema.
    """

    name = "groq"
    _ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: Type[OutputT],
        max_output_tokens: int = 1200,
        temperature: float = 0.2,
    ) -> ProviderResult:
        settings = self._settings
        if not settings.groq_api_key:
            raise RuntimeError("Groq is selected but GROQ_API_KEY is missing from backend/.env.")

        # Groq's json_object response format requires the literal word "json" to
        # appear in the messages, and the model needs the field list to produce a
        # schema-valid object. Build a system message that guarantees both.
        schema_hint = _json_schema_hint(schema)
        system_message = (
            f"{system_prompt}\n\n"
            "Respond with a single valid JSON object and nothing else. "
            f"The JSON object must contain exactly these top-level keys: {schema_hint}."
        )
        try:
            response = httpx.post(
                self._ENDPOINT,
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "max_completion_tokens": max_output_tokens,
                    "temperature": temperature,
                },
                timeout=settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            # Models frequently return comma-separated strings where a list field is
            # expected. Coerce against the schema before validation so these common,
            # recoverable formatting quirks do not fail the whole run.
            coerced = _coerce_to_schema(parsed, schema)
            validated = schema.model_validate(coerced)
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Groq request failed with HTTP {exc.response.status_code}.") from exc
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Groq returned an invalid or unavailable analysis response.") from exc

        usage = body.get("usage") or {}
        return ProviderResult(
            output=validated.model_dump(),
            usage={
                "provider": "groq",
                "model": body.get("model", settings.groq_model),
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
        )


class BedrockProvider:
    """Uses the strands-agents library with Amazon Bedrock.

    Requires AWS credentials in the backend environment. Structured output is
    produced through strands' ``Agent.structured_output``.
    """

    name = "bedrock"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _build_model(self):
        settings = self._settings
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            raise RuntimeError(
                "Bedrock model configuration is missing AWS credentials. "
                "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY or use a mocked provider in tests."
            )
        # Imported lazily so the mock/groq paths do not require boto3/strands at import time.
        from strands.models import BedrockModel

        return BedrockModel(
            model_id=settings.bedrock_model_id,
            region_name=settings.aws_region,
            api_key=settings.llm_api_key,
        )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: Type[OutputT],
        max_output_tokens: int = 1200,
        temperature: float = 0.2,
    ) -> ProviderResult:
        from strands import Agent

        agent = Agent(model=self._build_model(), system_prompt=system_prompt)
        validated = agent.structured_output(schema, prompt=user_prompt)
        return ProviderResult(output=validated.model_dump(), usage=None)


def get_provider(
    settings: Settings | None = None,
    *,
    mock_sample: dict[str, object] | None = None,
) -> LLMProvider:
    """Return the provider implementation selected by ``LLM_PROVIDER``.

    ``mock_sample`` lets an agent hand the mock provider a tailored, guardrail-safe
    payload. It is ignored by the live providers.

    Raises ``RuntimeError`` for an unknown provider name so configuration mistakes
    fail loudly instead of silently falling back.
    """
    settings = settings or get_settings()
    provider = settings.llm_provider.lower()
    if provider == "mock":
        return MockProvider(mock_sample)
    if provider == "groq":
        return GroqProvider(settings)
    if provider == "bedrock":
        return BedrockProvider(settings)
    raise RuntimeError(
        f"Unsupported LLM provider '{settings.llm_provider}'. "
        "Supported providers are: mock, groq, bedrock."
    )


def _json_schema_hint(schema: Type[BaseModel]) -> str:
    """Return a human-readable list of the schema's top-level field names."""
    return ", ".join(f'"{name}"' for name in schema.model_fields)


def _coerce_to_schema(data: object, schema: Type[BaseModel]) -> object:
    """Best-effort coercion of model JSON toward a Pydantic schema.

    Handles the most common LLM formatting quirks without masking real errors:
    - a scalar given where a ``list`` is expected is wrapped/split into a list
    - nested ``BaseModel`` fields and ``list[BaseModel]`` items recurse
    Values that already match are returned unchanged; anything unrecognized is
    passed through for normal Pydantic validation to accept or reject.
    """
    if not isinstance(data, dict):
        return data

    result: dict[str, object] = dict(data)
    for name, field in schema.model_fields.items():
        if name not in result:
            continue
        value = result[name]
        annotation = field.annotation
        inner_model = _inner_model(annotation)
        if _expects_list(annotation):
            items = _as_list(value)
            if inner_model is not None:
                items = [_coerce_to_schema(item, inner_model) for item in items]
            result[name] = items
        elif inner_model is not None and isinstance(value, dict):
            result[name] = _coerce_to_schema(value, inner_model)
    return result


def _expects_list(annotation: object) -> bool:
    import typing

    if annotation is list:
        return True
    origin = typing.get_origin(annotation)
    if origin is list:
        return True
    # Union types (e.g. ``str | dict | list``): list is acceptable but not required,
    # so do not force coercion — leave the model's shape for validation to accept.
    return False


def _inner_model(annotation: object) -> Type[BaseModel] | None:
    """Return the BaseModel type inside ``list[Model]`` or a bare ``Model``, else None."""
    import typing

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    for arg in typing.get_args(annotation):
        if isinstance(arg, type) and issubclass(arg, BaseModel):
            return arg
    return None


def _as_list(value: object) -> list:
    """Normalize a scalar, delimited string, or mapping into a list.

    A dict is flattened into its values (preferring object values, otherwise
    ``"key: value"`` strings) so a model that categorizes a list into an object
    still yields a usable list.
    """
    if isinstance(value, list):
        return value
    if value is None:
        return []
    if isinstance(value, dict):
        items: list = []
        for key, inner in value.items():
            if isinstance(inner, dict):
                items.append(inner)
            elif isinstance(inner, list):
                items.extend(inner)
            else:
                items.append(f"{key}: {inner}")
        return items or [value]
    if isinstance(value, str):
        # Split comma/semicolon/newline separated strings; otherwise wrap as one item.
        import re

        parts = [part.strip() for part in re.split(r"[;\n]|,(?![^(]*\))", value) if part.strip()]
        return parts or [value]
    return [value]


def _mock_sample_for(schema: Type[BaseModel]) -> dict[str, object]:
    """Build a minimal schema-shaped payload for the mock provider.

    Produces a placeholder value for each field based on its declared type so any
    agent output schema can be mocked without hand-written fixtures per agent.
    """
    sample: dict[str, object] = {}
    for field_name, field in schema.model_fields.items():
        annotation = field.annotation
        annotation_str = str(annotation)
        if "list" in annotation_str.lower():
            sample[field_name] = [f"sample {field_name.replace('_', ' ')}"]
        elif annotation in (int, float):
            sample[field_name] = 0
        elif annotation is bool:
            sample[field_name] = False
        else:
            sample[field_name] = (
                f"Mock {field_name.replace('_', ' ')} generated without a live model provider."
            )
    return sample

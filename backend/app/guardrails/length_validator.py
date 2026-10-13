"""
Length validator guardrail.

Enforces minimum and maximum word counts per artifact/agent type.
Catches both runaway verbose outputs and suspiciously terse ones.
"""
from __future__ import annotations

from typing import Any

from app.guardrails.base import GuardrailResult, GuardrailViolation, Severity

# agent_name → (min_words, max_words)
LENGTH_LIMITS: dict[str, tuple[int, int]] = {
    "idea_analyst":          (30,   2_000),
    "market_research":       (100,  5_000),
    "technical_feasibility": (100,  5_000),
    "prd_generator":         (200, 15_000),
    "architecture_agent":    (150, 10_000),
    "ux_spec_agent":         (100,  8_000),
    "quality_evaluator":     (50,   5_000),
}

_DEFAULT_LIMITS: tuple[int, int] = (10, 20_000)


def _word_count(output: Any) -> int:
    if isinstance(output, str):
        return len(output.split())
    if isinstance(output, dict):
        return sum(_word_count(v) for v in output.values())
    if isinstance(output, list):
        return sum(_word_count(item) for item in output)
    return len(str(output).split())


def check_length(output: Any, agent_name: str) -> GuardrailResult:
    """
    Validate that output word count is within acceptable bounds for the agent type.
    """
    result = GuardrailResult(passed=True)
    min_words, max_words = LENGTH_LIMITS.get(agent_name, _DEFAULT_LIMITS)
    count = _word_count(output)

    if count < min_words:
        result.add_violation(GuardrailViolation(
            rule_name="output_too_short",
            severity=Severity.HIGH,
            message=(
                f"Agent '{agent_name}' output is too short "
                f"({count} words, minimum {min_words})."
            ),
            detail={"word_count": count, "min_words": min_words, "agent": agent_name},
        ))

    if count > max_words:
        result.add_violation(GuardrailViolation(
            rule_name="output_too_long",
            severity=Severity.LOW,
            message=(
                f"Agent '{agent_name}' output exceeds recommended length "
                f"({count} words, maximum {max_words})."
            ),
            detail={"word_count": count, "max_words": max_words, "agent": agent_name},
        ))

    return result

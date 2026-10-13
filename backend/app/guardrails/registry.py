"""
Guardrail registry.

Defines which guardrails run for each agent and in what order.
`run_guardrails` is the single entry point used by services and the orchestrator.
"""
from __future__ import annotations

from typing import Any

from app.guardrails.base import GuardrailResult, GuardrailViolation, Severity
from app.guardrails.content_filter import check_content
from app.guardrails.length_validator import check_length
from app.guardrails.schema_validator import check_schema
from app.guardrails.scope_validator import check_scope


def _merge(base: GuardrailResult, other: GuardrailResult) -> GuardrailResult:
    """Merge violations from `other` into `base`."""
    for v in other.violations:
        base.add_violation(v)
    return base


def run_guardrails(
    output: Any,
    agent_name: str,
    *,
    idea: str = "",
) -> GuardrailResult:
    """
    Run the full guardrail chain for the given agent and output.

    Parameters
    ----------
    output:
        The raw dict (or any structure) returned by the agent.
    agent_name:
        Identifies which schema/length rules to apply.
    idea:
        The original project idea text, used for scope validation.

    Returns
    -------
    GuardrailResult
        .passed         — True only if zero violations were found.
        .safe_to_proceed — True if no HIGH/CRITICAL violations exist
                          (LOW/MEDIUM violations are warnings, not blockers).
        .violations     — list of all GuardrailViolation instances.
    """
    result = GuardrailResult(passed=True)

    # 1. Content safety — always runs first (highest priority)
    _merge(result, check_content(output, agent_name))

    # 2. Schema validation — structure must be correct
    _merge(result, check_schema(output, agent_name))

    # 3. Scope validation — output must relate to the idea
    if idea:
        _merge(result, check_scope(output, idea, agent_name))

    # 4. Length validation — output size must be within bounds
    _merge(result, check_length(output, agent_name))

    return result

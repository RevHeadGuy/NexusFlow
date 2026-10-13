"""
Schema validator guardrail.

Ensures that an agent's output dict contains the required top-level keys
and that list fields are non-empty where expected.
"""
from __future__ import annotations

from typing import Any

from app.guardrails.base import GuardrailResult, GuardrailViolation, Severity

# Maps agent_name → (required_keys, non_empty_list_keys)
AGENT_SCHEMAS: dict[str, tuple[list[str], list[str]]] = {
    "idea_analyst": (
        ["problem_statement", "target_users", "goals", "constraints", "success_criteria"],
        ["target_users", "goals", "constraints", "success_criteria"],
    ),
    "market_research": (
        ["competitors", "market_size", "user_personas", "opportunities", "risks"],
        ["competitors", "user_personas"],
    ),
    "technical_feasibility": (
        ["recommended_stack", "build_vs_buy", "complexity_score", "technical_risks"],
        ["recommended_stack", "technical_risks"],
    ),
    "prd_generator": (
        ["title", "overview", "features", "user_stories", "acceptance_criteria"],
        ["features", "user_stories"],
    ),
    "architecture_agent": (
        ["components", "data_flow", "tech_stack", "infrastructure"],
        ["components", "tech_stack"],
    ),
    "ux_spec_agent": (
        ["user_flows", "screens", "interaction_patterns"],
        ["user_flows", "screens"],
    ),
    "quality_evaluator": (
        ["findings", "summary", "overall_score"],
        ["findings"],
    ),
}


def check_schema(output: Any, agent_name: str) -> GuardrailResult:
    """
    Validate that the output dict matches the expected schema for the given agent.
    """
    result = GuardrailResult(passed=True)

    if agent_name not in AGENT_SCHEMAS:
        # No schema defined for this agent — skip validation
        return result

    required_keys, non_empty_keys = AGENT_SCHEMAS[agent_name]

    if not isinstance(output, dict):
        result.add_violation(GuardrailViolation(
            rule_name="schema_type_error",
            severity=Severity.CRITICAL,
            message=f"Agent '{agent_name}' output must be a dict, got {type(output).__name__}.",
            detail={"agent": agent_name, "actual_type": type(output).__name__},
        ))
        return result  # No point checking keys on a non-dict

    # Check required keys are present and not None/empty string
    missing: list[str] = []
    for key in required_keys:
        if key not in output or output[key] is None or output[key] == "":
            missing.append(key)

    if missing:
        result.add_violation(GuardrailViolation(
            rule_name="schema_missing_fields",
            severity=Severity.HIGH,
            message=f"Agent '{agent_name}' output is missing required fields: {missing}.",
            detail={"missing_fields": missing, "agent": agent_name},
        ))

    # Check list fields are non-empty
    empty_lists: list[str] = []
    for key in non_empty_keys:
        if key in output and isinstance(output[key], list) and len(output[key]) == 0:
            empty_lists.append(key)

    if empty_lists:
        result.add_violation(GuardrailViolation(
            rule_name="schema_empty_list_fields",
            severity=Severity.MEDIUM,
            message=f"Agent '{agent_name}' returned empty list(s) for: {empty_lists}.",
            detail={"empty_fields": empty_lists, "agent": agent_name},
        ))

    return result

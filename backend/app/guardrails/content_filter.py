"""
Content filter guardrail.

Checks agent output text for:
  - Prompt injection attempts (instructions embedded in LLM output)
  - Toxic / harmful language patterns
  - Exposed secrets / credentials
  - PII patterns (emails, phone numbers, SSNs)
"""
from __future__ import annotations

import re
from typing import Any

from app.guardrails.base import GuardrailResult, GuardrailViolation, Severity

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Prompt injection — common jailbreak / override phrases embedded in output
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore (previous|all|prior) instructions?", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"disregard (your|the) (system|previous|prior) prompt", re.IGNORECASE),
    re.compile(r"act as (a|an) (?!product|engineer|researcher)", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"\[\s*INST\s*\]", re.IGNORECASE),
]

# Obvious credential / secret leakage patterns
_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(aws_secret_access_key|aws_access_key_id)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"(password|passwd|secret|token|api_key)\s*[:=]\s*['\"]?\S{8,}['\"]?", re.IGNORECASE),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"sk-[A-Za-z0-9]{32,}"),   # OpenAI-style key pattern
    re.compile(r"AKIA[0-9A-Z]{16}"),        # AWS access key ID
]

# PII patterns
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b")),
    ("phone", re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("ssn",   re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit_card", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
]

# Profanity / toxic — kept minimal, extend as needed
_TOXIC_TERMS: list[str] = [
    "kill yourself", "kys", "you should die",
]


def _flatten_output(output: Any) -> str:
    """Recursively flatten any output structure to a single string for scanning."""
    if isinstance(output, str):
        return output
    if isinstance(output, dict):
        return " ".join(_flatten_output(v) for v in output.values())
    if isinstance(output, list):
        return " ".join(_flatten_output(item) for item in output)
    return str(output)


def check_content(output: Any, agent_name: str = "unknown") -> GuardrailResult:
    """
    Run all content filters against the agent output.
    Returns a GuardrailResult with any violations found.
    """
    result = GuardrailResult(passed=True)
    text = _flatten_output(output)

    # Prompt injection
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            result.add_violation(GuardrailViolation(
                rule_name="prompt_injection",
                severity=Severity.CRITICAL,
                message=f"Possible prompt injection detected in output from '{agent_name}'.",
                detail={"match": match.group(0), "agent": agent_name},
            ))
            break  # one violation per category is enough

    # Secret leakage
    for pattern in _SECRET_PATTERNS:
        match = pattern.search(text)
        if match:
            result.add_violation(GuardrailViolation(
                rule_name="secret_leakage",
                severity=Severity.CRITICAL,
                message=f"Possible credential or secret pattern found in output from '{agent_name}'.",
                detail={"pattern": pattern.pattern[:40], "agent": agent_name},
            ))
            break

    # PII detection
    pii_found: list[str] = []
    for pii_type, pattern in _PII_PATTERNS:
        if pattern.search(text):
            pii_found.append(pii_type)

    if pii_found:
        result.add_violation(GuardrailViolation(
            rule_name="pii_detected",
            severity=Severity.HIGH,
            message=f"PII detected in output from '{agent_name}': {', '.join(pii_found)}.",
            detail={"pii_types": pii_found, "agent": agent_name},
        ))

    # Toxic language
    text_lower = text.lower()
    for term in _TOXIC_TERMS:
        if term in text_lower:
            result.add_violation(GuardrailViolation(
                rule_name="toxic_language",
                severity=Severity.HIGH,
                message=f"Toxic language detected in output from '{agent_name}'.",
                detail={"term": term, "agent": agent_name},
            ))
            break

    return result

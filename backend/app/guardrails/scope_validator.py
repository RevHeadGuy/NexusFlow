"""
Scope validator guardrail.

Checks that agent output is meaningfully related to the original project idea.
Uses simple keyword overlap — no LLM call required, keeping this deterministic and fast.

For production, this can be upgraded to an embedding-based similarity check.
"""
from __future__ import annotations

import re
from typing import Any

from app.guardrails.base import GuardrailResult, GuardrailViolation, Severity

# Words that carry no semantic weight for overlap scoring
_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
    "it", "its", "this", "that", "to", "of", "in", "on", "at", "for",
    "with", "by", "from", "as", "be", "have", "has", "had", "will",
    "would", "could", "should", "may", "might", "can", "do", "does",
    "did", "not", "no", "we", "our", "you", "your", "they", "their",
    "i", "my", "me", "he", "she", "his", "her", "us", "up", "out",
    "about", "which", "who", "all", "also", "more", "than", "into",
    "each", "when", "so", "what", "how", "if", "then", "than",
})

# Minimum Jaccard similarity between idea tokens and output tokens
_MIN_JACCARD: float = 0.05  # Intentionally low — just catches completely off-topic output


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z]+", text.lower())
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 2}


def _flatten(output: Any) -> str:
    if isinstance(output, str):
        return output
    if isinstance(output, dict):
        return " ".join(_flatten(v) for v in output.values())
    if isinstance(output, list):
        return " ".join(_flatten(item) for item in output)
    return str(output)


def check_scope(output: Any, idea: str, agent_name: str = "unknown") -> GuardrailResult:
    """
    Verify that the output is topically related to the original project idea.
    """
    result = GuardrailResult(passed=True)

    if not idea or not idea.strip():
        # Nothing to compare against — skip
        return result

    idea_tokens = _tokenize(idea)
    output_tokens = _tokenize(_flatten(output))

    if not output_tokens:
        result.add_violation(GuardrailViolation(
            rule_name="scope_empty_output",
            severity=Severity.HIGH,
            message=f"Agent '{agent_name}' produced no meaningful text content.",
            detail={"agent": agent_name},
        ))
        return result

    intersection = idea_tokens & output_tokens
    union = idea_tokens | output_tokens
    jaccard = len(intersection) / len(union) if union else 0.0

    if jaccard < _MIN_JACCARD:
        result.add_violation(GuardrailViolation(
            rule_name="scope_mismatch",
            severity=Severity.MEDIUM,
            message=(
                f"Agent '{agent_name}' output may be off-topic "
                f"(similarity score: {jaccard:.3f}, threshold: {_MIN_JACCARD})."
            ),
            detail={
                "jaccard_score": round(jaccard, 4),
                "threshold": _MIN_JACCARD,
                "agent": agent_name,
                "idea_sample": idea[:120],
            },
        ))

    return result

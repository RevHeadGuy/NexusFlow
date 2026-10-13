from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GuardrailViolation:
    rule_name: str
    severity: Severity
    message: str
    # Extra evidence — e.g. the offending snippet or field name
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class GuardrailResult:
    passed: bool
    violations: list[GuardrailViolation] = field(default_factory=list)

    # Convenience — True only when there are no CRITICAL or HIGH violations
    @property
    def safe_to_proceed(self) -> bool:
        blocking = {Severity.CRITICAL, Severity.HIGH}
        return all(v.severity not in blocking for v in self.violations)

    def add_violation(self, violation: GuardrailViolation) -> None:
        self.violations.append(violation)
        self.passed = False

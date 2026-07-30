from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class RuleSeverity(str, Enum):
    """Severity levels for security rule violations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleResult(BaseModel):
    """Result payload produced by an individual security rule evaluation."""

    matched: bool = Field(..., description="Flag indicating if the security rule was matched/triggered")
    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    severity: RuleSeverity = Field(default=RuleSeverity.MEDIUM, description="Rule severity rating")
    risk_score: float = Field(default=0.0, description="Risk contribution score between 0.0 and 1.0")
    violation: str | None = Field(default=None, description="Specific security policy violation details")
    recommendation: str | None = Field(default=None, description="Suggested remediation action")
    reason: str | None = Field(default=None, description="Explanation for rule match or pass")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional rule execution metadata")

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from tools.schemas import ToolRequest


class PolicyDecision(str, Enum):
    """Policy decision enum for Agent WAF rule enforcement."""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


class InspectionContext(BaseModel):
    """Context model capturing normalized tool request state for security inspection."""

    tool_name: str = Field(default="unknown", description="Target tool name being invoked")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Input parameters passed to the tool")
    agent_id: str | None = Field(default=None, description="Calling agent identifier")
    request_id: str | None = Field(default=None, description="Correlation request ID")
    session_id: str | None = Field(default=None, description="Agent session ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Context metadata")
    timestamp: Any = Field(default=None, description="UTC ISO 8601 timestamp of inspection start")


class PolicyEvaluationResult(BaseModel):
    """Result model containing multi-rule policy decision details, violations, and risk metrics."""

    decision: PolicyDecision = Field(..., description="Security decision (ALLOW or BLOCK)")
    reason: str | None = Field(default=None, description="Detailed explanation of the policy decision")
    risk_score: float = Field(default=0.0, description="Calculated risk score between 0.0 and 1.0")
    rule_id: str | None = Field(default=None, description="Primary matched rule ID")
    matched_rules: list[str] = Field(default_factory=list, description="List of all matched policy rule identifiers")
    violations: list[str] = Field(default_factory=list, description="List of specific security policy violations detected")
    recommendations: list[str] = Field(default_factory=list, description="Remediation recommendations for blocked or flagged requests")
    evaluation_time_ms: float = Field(default=0.0, description="Duration of policy evaluation in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Context metadata from rule evaluation")


class BasePolicyEvaluator(ABC):
    """Abstract base evaluator protocol for inspecting tool requests."""

    @abstractmethod
    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> PolicyEvaluationResult:
        """Evaluate security policies against incoming tool request."""
        pass


class DefaultPolicyEvaluator(BasePolicyEvaluator):
    """Default permissive policy evaluator returning ALLOW decision."""

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> PolicyEvaluationResult:
        return PolicyEvaluationResult(
            decision=PolicyDecision.ALLOW,
            risk_score=0.0,
            reason="Default permissive policy evaluator",
        )

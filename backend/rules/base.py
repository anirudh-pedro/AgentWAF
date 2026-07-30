from abc import ABC, abstractmethod
from typing import Any

from proxy.models import InspectionContext
from tools.schemas import ToolRequest
from .models import RuleResult, RuleSeverity


class BaseRule(ABC):
    """Abstract base class that every Agent WAF security rule must implement."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier of the rule (e.g., RULE-PROMPT-INJ-001)."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the rule."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the security threat or check performed by this rule."""
        pass

    @property
    @abstractmethod
    def severity(self) -> RuleSeverity:
        """Severity level associated with rule violations."""
        pass

    @property
    def priority(self) -> int:
        """Execution priority order (lower value = higher priority). Default 100."""
        return 100

    @property
    def stop_on_match(self) -> bool:
        """If True, matching this rule immediately short-circuits rule evaluation."""
        return False

    @property
    def tags(self) -> list[str]:
        """Tags for security policy classification and dashboard analytics."""
        return ["security"]

    @property
    def enabled(self) -> bool:
        """Flag indicating if this rule is currently enabled for evaluation."""
        return True

    @abstractmethod
    async def evaluate(
        self, request: ToolRequest, context: InspectionContext
    ) -> RuleResult:
        """Evaluate a tool request and inspection context against the security rule."""
        pass

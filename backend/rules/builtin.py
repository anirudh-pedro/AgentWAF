import re
from typing import Any

from config import get_settings
from proxy.models import InspectionContext
from tools import ToolRegistry
from tools.schemas import ToolRequest
from .base import BaseRule
from .models import RuleResult, RuleSeverity


def _extract_all_strings(obj: Any, current_depth: int = 0, max_depth: int = 10) -> list[str]:
    """Recursively extract all string values from nested dictionaries and lists."""
    if current_depth > max_depth:
        return []

    strings: list[str] = []
    if isinstance(obj, str):
        strings.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                strings.append(k)
            strings.extend(_extract_all_strings(v, current_depth + 1, max_depth))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            strings.extend(_extract_all_strings(item, current_depth + 1, max_depth))
    return strings


def _calculate_max_depth(obj: Any, current_depth: int = 1) -> int:
    """Calculate the maximum nesting depth of a dictionary or list structure."""
    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(_calculate_max_depth(v, current_depth + 1) for v in obj.values())
    elif isinstance(obj, (list, tuple)):
        if not obj:
            return current_depth
        return max(_calculate_max_depth(item, current_depth + 1) for item in obj)
    return current_depth


class PromptInjectionRule(BaseRule):
    """Detects prompt injection attack patterns in tool arguments."""

    _PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
        re.compile(r"system\s+prompt", re.IGNORECASE),
        re.compile(r"developer\s+message", re.IGNORECASE),
        re.compile(r"reveal\s+prompt", re.IGNORECASE),
        re.compile(r"override\s+instructions", re.IGNORECASE),
        re.compile(r"act\s+as\s+system", re.IGNORECASE),
        re.compile(r"disregard\s+all\s+prior", re.IGNORECASE),
    )

    @property
    def rule_id(self) -> str:
        return "RULE-SEC-PROMPT-INJ-001"

    @property
    def name(self) -> str:
        return "Prompt Injection Detector"

    @property
    def description(self) -> str:
        return "Detects malicious prompt injection patterns in tool invocation arguments."

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.CRITICAL

    @property
    def priority(self) -> int:
        return 10

    @property
    def stop_on_match(self) -> bool:
        return True

    @property
    def tags(self) -> list[str]:
        return ["prompt", "llm", "injection", "high-risk"]

    @property
    def enabled(self) -> bool:
        return get_settings().PROMPT_INJECTION_ENABLED

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> RuleResult:
        all_strings = _extract_all_strings(request.parameters)

        for text in all_strings:
            for pattern in self._PATTERNS:
                if pattern.search(text):
                    return RuleResult(
                        matched=True,
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        severity=self.severity,
                        risk_score=0.9,
                        violation=f"Potential prompt injection pattern matched: '{pattern.pattern}'",
                        recommendation="Block execution and log security event for prompt analysis",
                        reason="Input parameter contains instructions attempting to override system prompts",
                        metadata={"matched_pattern": pattern.pattern},
                    )

        return RuleResult(
            matched=False,
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=self.severity,
            risk_score=0.0,
            reason="No prompt injection patterns detected",
        )


class SQLInjectionRule(BaseRule):
    """Detects SQL injection payload patterns in tool arguments."""

    _PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b", re.IGNORECASE),
        re.compile(r"(\'|\")\s*OR\s*(\'|\")?\d+(\'|\")?\s*=\s*(\'|\")?\d+", re.IGNORECASE),
        re.compile(r";\s*--", re.IGNORECASE),
        re.compile(r"/\*.*?\*/", re.IGNORECASE),
        re.compile(r"\bxp_\w+", re.IGNORECASE),
    )

    @property
    def rule_id(self) -> str:
        return "RULE-SEC-SQL-INJ-002"

    @property
    def name(self) -> str:
        return "SQL Injection Detector"

    @property
    def description(self) -> str:
        return "Detects malicious SQL injection syntax and commands in tool parameters."

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.CRITICAL

    @property
    def priority(self) -> int:
        return 20

    @property
    def stop_on_match(self) -> bool:
        return True

    @property
    def tags(self) -> list[str]:
        return ["sql", "database", "injection", "high-risk"]

    @property
    def enabled(self) -> bool:
        return get_settings().SQL_INJECTION_ENABLED

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> RuleResult:
        all_strings = _extract_all_strings(request.parameters)

        for text in all_strings:
            for pattern in self._PATTERNS:
                if pattern.search(text):
                    return RuleResult(
                        matched=True,
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        severity=self.severity,
                        risk_score=0.85,
                        violation=f"Potential SQL injection syntax matched: '{pattern.pattern}'",
                        recommendation="Block execution and sanitize parameter inputs",
                        reason="Input parameter contains raw SQL syntax or statement delimiters",
                        metadata={"matched_pattern": pattern.pattern},
                    )

        return RuleResult(
            matched=False,
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=self.severity,
            risk_score=0.0,
            reason="No SQL injection payloads detected",
        )


class DangerousToolRule(BaseRule):
    """Blocks tool execution if tool belongs to prohibited high-risk tool categories."""

    @property
    def rule_id(self) -> str:
        return "RULE-SEC-DANGEROUS-TOOL-003"

    @property
    def name(self) -> str:
        return "Dangerous Tool Category Policy"

    @property
    def description(self) -> str:
        return "Prohibits invocation of tools belonging to restricted categories."

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def priority(self) -> int:
        return 30

    @property
    def tags(self) -> list[str]:
        return ["tool", "access-control", "category"]

    @property
    def enabled(self) -> bool:
        return get_settings().DANGEROUS_TOOL_ENABLED

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> RuleResult:
        settings = get_settings()
        denied_categories = {cat.lower().strip() for cat in settings.DENIED_TOOL_CATEGORIES}

        tool_category = "unknown"
        try:
            tool = ToolRegistry.get_instance().get(request.tool_name)
            tool_category = tool.category.lower().strip()
        except KeyError:
            pass

        if tool_category in denied_categories or request.tool_name.lower().strip() in denied_categories:
            return RuleResult(
                matched=True,
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                risk_score=0.8,
                violation=f"Tool '{request.tool_name}' belongs to prohibited category '{tool_category}'",
                recommendation="Deny access to system-level/filesystem tools",
                reason="Tool category is present in settings.DENIED_TOOL_CATEGORIES",
                metadata={"tool_category": tool_category, "denied_categories": list(denied_categories)},
            )

        return RuleResult(
            matched=False,
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=self.severity,
            risk_score=0.0,
            reason="Tool category permitted by policy",
        )


class ParameterSizeRule(BaseRule):
    """Enforces parameter length and nesting depth limits to prevent DoS attacks."""

    @property
    def rule_id(self) -> str:
        return "RULE-SEC-PARAM-SIZE-004"

    @property
    def name(self) -> str:
        return "Parameter Size & Nesting Limit Policy"

    @property
    def description(self) -> str:
        return "Rejects requests with oversized string parameters or excessive dictionary nesting."

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MEDIUM

    @property
    def priority(self) -> int:
        return 50

    @property
    def tags(self) -> list[str]:
        return ["dos", "parameters", "limits"]

    @property
    def enabled(self) -> bool:
        return get_settings().PARAMETER_SIZE_ENABLED

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> RuleResult:
        settings = get_settings()
        all_strings = _extract_all_strings(request.parameters)

        for text in all_strings:
            if len(text) > settings.MAX_PARAMETER_LENGTH:
                return RuleResult(
                    matched=True,
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    severity=self.severity,
                    risk_score=0.6,
                    violation=f"Parameter string length ({len(text)}) exceeds maximum allowed ({settings.MAX_PARAMETER_LENGTH})",
                    recommendation="Truncate parameter length or reject request",
                    reason="Excessive parameter string length detected",
                    metadata={"param_len": len(text), "max_allowed": settings.MAX_PARAMETER_LENGTH},
                )

        depth = _calculate_max_depth(request.parameters)
        if depth > settings.MAX_PARAMETER_DEPTH:
            return RuleResult(
                matched=True,
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                risk_score=0.6,
                violation=f"Parameter nesting depth ({depth}) exceeds maximum allowed ({settings.MAX_PARAMETER_DEPTH})",
                recommendation="Flatten input parameter structure",
                reason="Excessive parameter nesting depth detected",
                metadata={"nesting_depth": depth, "max_allowed": settings.MAX_PARAMETER_DEPTH},
            )

        return RuleResult(
            matched=False,
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=self.severity,
            risk_score=0.0,
            reason="Parameter size and depth within limits",
        )

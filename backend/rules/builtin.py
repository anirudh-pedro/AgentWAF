import re
import time
from collections import defaultdict
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


def _extract_string_values_only(obj: Any, current_depth: int = 0, max_depth: int = 10) -> list[str]:
    """Recursively extract ONLY parameter values (ignoring dictionary keys)."""
    if current_depth > max_depth:
        return []

    strings: list[str] = []
    if isinstance(obj, str):
        strings.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            strings.extend(_extract_string_values_only(v, current_depth + 1, max_depth))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            strings.extend(_extract_string_values_only(item, current_depth + 1, max_depth))
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
        re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
        re.compile(r"system\s+override", re.IGNORECASE),
        re.compile(r"system\s+prompt", re.IGNORECASE),
        re.compile(r"developer\s+(mode|message)", re.IGNORECASE),
        re.compile(r"reveal\s+(prompt|keys|credentials|secrets)", re.IGNORECASE),
        re.compile(r"override\s+(instructions|policy|policies|security|firewall)", re.IGNORECASE),
        re.compile(r"act\s+as\s+(system|admin|root|jailbroken)", re.IGNORECASE),
        re.compile(r"disregard\s+(all\s+)?prior", re.IGNORECASE),
        re.compile(r"jailbreak", re.IGNORECASE),
        re.compile(r"disable\s+(firewall|security|policy|policies)", re.IGNORECASE),
        re.compile(r"bypass\s+.*(waf|firewall|policy|policies|security|rule|rules|guard|agent)", re.IGNORECASE),
        re.compile(r"bypassing\s+(agent|waf|policy|security)", re.IGNORECASE),
        re.compile(r"allowed\s+to\s+bypass", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(allowed|authorized|permitted)", re.IGNORECASE),
        re.compile(r"forget\s+(your|all|previous|prior)\s+instructions", re.IGNORECASE),
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
        re.compile(r"\b(UNION\s+SELECT|SELECT\s+.*\s+FROM|INSERT\s+INTO|DELETE\s+FROM|DROP\s+(TABLE|DATABASE)|TRUNCATE\s+TABLE|ALTER\s+TABLE)\b", re.IGNORECASE),
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
    """Blocks tool execution if tool belongs to prohibited high-risk tool categories or contains destructive commands."""

    _DANGEROUS_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"rm\s+-rf", re.IGNORECASE),
        re.compile(r"drop\s+database", re.IGNORECASE),
        re.compile(r"delete\s+every\s+database", re.IGNORECASE),
        re.compile(r"drop\s+table", re.IGNORECASE),
        re.compile(r"remove\s+all\s+files", re.IGNORECASE),
        re.compile(r"format\s+[c-z]:", re.IGNORECASE),
        re.compile(r"bash\s+script", re.IGNORECASE),
        re.compile(r"shell\s+command", re.IGNORECASE),
    )

    @property
    def rule_id(self) -> str:
        return "RULE-SEC-DANGEROUS-TOOL-003"

    @property
    def name(self) -> str:
        return "Dangerous Tool Category Policy"

    @property
    def description(self) -> str:
        return "Prohibits invocation of tools belonging to restricted categories or containing destructive shell/database actions."

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

        # 1. Category and tool name denial
        if tool_category in denied_categories or request.tool_name.lower().strip() in denied_categories or request.tool_name.lower().strip() in ("shell", "bash", "terminal", "system"):
            return RuleResult(
                matched=True,
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                risk_score=0.8,
                violation=f"Requested tool '{request.tool_name}' belongs to denied category or restricted tool set",
                recommendation="Deny access to system-level/filesystem/shell tools",
                reason="Tool category or tool name is present in settings.DENIED_TOOL_CATEGORIES",
                metadata={"tool_category": tool_category, "denied_categories": list(denied_categories)},
            )

        # 2. Destructive command pattern denial
        all_strings = _extract_all_strings(request.parameters)
        for text in all_strings:
            for pattern in self._DANGEROUS_PATTERNS:
                if pattern.search(text):
                    return RuleResult(
                        matched=True,
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        severity=self.severity,
                        risk_score=0.85,
                        violation=f"Destructive or prohibited command pattern matched: '{pattern.pattern}'",
                        recommendation="Block execution of destructive shell or database commands",
                        reason="Parameter contains prohibited high-risk command syntax",
                        metadata={"matched_pattern": pattern.pattern},
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
        return 1

    @property
    def tags(self) -> list[str]:
        return ["dos", "parameters", "limits", "safeguard"]

    @property
    def enabled(self) -> bool:
        return get_settings().PARAMETER_SIZE_ENABLED

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> RuleResult:
        settings = get_settings()
        max_len = settings.MAX_PARAMETER_LENGTH  # Default 5000 chars

        # 1. Total serialized payload length check
        param_payload_str = str(request.parameters)
        if len(param_payload_str) > max_len:
            return RuleResult(
                matched=True,
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=RuleSeverity.CRITICAL,
                risk_score=0.9,
                violation=f"Input payload total length ({len(param_payload_str)} chars) exceeds maximum allowed safeguard threshold ({max_len} chars)",
                recommendation="Truncate request parameter payload or split into smaller requests",
                reason=f"Input payload exceeds maximum safeguard limit of {max_len} characters (ReDoS / Payload Safeguard)",
                metadata={"payload_len": len(param_payload_str), "max_allowed": max_len},
            )

        # 2. Individual parameter string length check
        all_strings = _extract_all_strings(request.parameters)
        for text in all_strings:
            if len(text) > max_len:
                return RuleResult(
                    matched=True,
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    severity=RuleSeverity.CRITICAL,
                    risk_score=0.9,
                    violation=f"Parameter string length ({len(text)} chars) exceeds maximum allowed safeguard threshold ({max_len} chars)",
                    recommendation="Truncate parameter length or reject request",
                    reason=f"Input parameter string length exceeds maximum safeguard threshold of {max_len} characters",
                    metadata={"param_len": len(text), "max_allowed": max_len},
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


class DataScopeRule(BaseRule):
    """Enforces data scope boundaries (RULE-SEC-DATA-SCOPE-005).

    Rejects tool calls that reference resources (customer IDs, document IDs, project IDs,
    dataset IDs, resource IDs) outside the agent's declared scope.
    """

    _RESOURCE_PATTERN = re.compile(
        r"\b(customer|doc|document|project|dataset|resource)_[a-zA-Z0-9_-]+\b",
        re.IGNORECASE,
    )
    _OUT_OF_SCOPE_PATHS = (
        re.compile(r"etc/passwd|/etc/shadow|c:\\windows\\system32", re.IGNORECASE),
        re.compile(r"scope\s*=\s*(admin|system|internal_root)", re.IGNORECASE),
    )

    @property
    def rule_id(self) -> str:
        return "RULE-SEC-DATA-SCOPE-005"

    @property
    def name(self) -> str:
        return "Data Scope Boundary Policy"

    @property
    def description(self) -> str:
        return "Rejects requests that attempt to access resources outside the agent's declared scope."

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def priority(self) -> int:
        return 45

    @property
    def tags(self) -> list[str]:
        return ["scope", "tenant", "authorization", "resource"]

    @property
    def enabled(self) -> bool:
        return True

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> RuleResult:
        settings = get_settings()
        
        # 1. Determine permitted scopes from context metadata or settings
        permitted_scopes: set[str] = set()
        if context.metadata and "permitted_scopes" in context.metadata:
            permitted_scopes = {str(s).lower() for s in context.metadata["permitted_scopes"]}
        elif request.metadata and "permitted_scopes" in request.metadata:
            permitted_scopes = {str(s).lower() for s in request.metadata["permitted_scopes"]}
        else:
            permitted_scopes = {s.lower() for s in settings.PERMITTED_DATA_SCOPES}

        # Also permit request's own agent_scope if specified
        agent_scope = request.metadata.get("agent_scope") or context.metadata.get("agent_scope")
        if agent_scope:
            permitted_scopes.add(str(agent_scope).lower())

        param_values_only = _extract_string_values_only(request.parameters)

        # 2. Check forbidden system path patterns
        for text in param_values_only:
            for forbidden_pattern in self._OUT_OF_SCOPE_PATHS:
                if forbidden_pattern.search(text):
                    return RuleResult(
                        matched=True,
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        severity=self.severity,
                        risk_score=0.8,
                        violation="Requested resource is outside the permitted agent scope.",
                        recommendation="Block execution due to data scope boundary violation",
                        reason="Requested resource is outside the permitted agent scope.",
                        metadata={"matched_pattern": forbidden_pattern.pattern},
                    )

        # 3. Extract resource IDs from values and verify against permitted scopes
        referenced_resources: list[str] = []
        for text in param_values_only:
            for match in self._RESOURCE_PATTERN.finditer(text):
                res_id = match.group(0).lower()
                referenced_resources.append(res_id)
                if res_id not in permitted_scopes:
                    return RuleResult(
                        matched=True,
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        severity=self.severity,
                        risk_score=0.8,
                        violation=f"Requested resource '{res_id}' is outside the permitted agent scope.",
                        recommendation="Block access to unauthorized customer/project/document resource",
                        reason="Requested resource is outside the permitted agent scope.",
                        metadata={
                            "requested_resource": res_id,
                            "permitted_scopes": list(permitted_scopes),
                        },
                    )

        return RuleResult(
            matched=False,
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=self.severity,
            risk_score=0.0,
            reason="All referenced resources are within permitted agent scope",
            metadata={"referenced_resources": referenced_resources},
        )


class SequenceRule(BaseRule):
    """Enforces execution sequence dependencies (RULE-SEC-SEQUENCE-006).

    Ensures certain tools may only execute after prerequisite tools (e.g. search_files -> download_file).
    Tracks session history in memory.
    """

    _session_history: dict[str, list[str]] = defaultdict(list)

    @classmethod
    def get_session_history(cls, session_id: str) -> list[str]:
        """Return sequence tool history for session."""
        return cls._session_history.get(session_id, [])

    @classmethod
    def clear_session_history(cls, session_id: str | None = None) -> None:
        """Clear sequence history for testing."""
        if session_id:
            cls._session_history.pop(session_id, None)
        else:
            cls._session_history.clear()

    @property
    def rule_id(self) -> str:
        return "RULE-SEC-SEQUENCE-006"

    @property
    def name(self) -> str:
        return "Tool Sequence Dependency Policy"

    @property
    def description(self) -> str:
        return "Enforces that sensitive tools require prerequisite tools to be called first in session."

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def priority(self) -> int:
        return 48

    @property
    def tags(self) -> list[str]:
        return ["sequence", "workflow", "stateful"]

    @property
    def enabled(self) -> bool:
        return True

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> RuleResult:
        session_id = request.session_id or request.agent_id or "default-session"
        current_tool = request.tool_name.lower().strip()
        history = self._session_history[session_id]
        previous_tool = history[-1] if history else None

        # Sequence Prerequisite Map (normalized keys & values: no underscores, lower)
        norm_prerequisites: dict[str, str] = {
            "downloadfile": "searchfiles",
            "download_file": "search_files",
            "downloadinvoice": "searchinvoice",
            "download": "search",
            "query_database": "authenticate",
            "commit": "stage",
            "admin_exec": "auth",
            "deleterecords": "auth",
        }

        norm_current = current_tool.replace("_", "").lower()
        norm_history = [t.replace("_", "").lower() for t in history]

        if norm_current in norm_prerequisites:
            required_norm = norm_prerequisites[norm_current]
            if required_norm not in norm_history:
                return RuleResult(
                    matched=True,
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    severity=self.severity,
                    risk_score=0.85,
                    violation=f"Sequence violation: Tool '{request.tool_name}' requires prerequisite tool '{required_norm}'",
                    recommendation="Block execution until prerequisite tool is executed first in this session",
                    reason=f"Sequence violation: '{request.tool_name}' executed without prior '{required_norm}'",
                    metadata={
                        "required_tool": required_norm,
                        "previous_tool": previous_tool,
                        "current_tool": request.tool_name,
                        "sequence_status": "VIOLATION",
                    },
                )

        # Append current tool to in-memory session sequence
        self._session_history[session_id].append(current_tool)
        return RuleResult(
            matched=False,
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=self.severity,
            risk_score=0.0,
            reason="Tool sequence order validated",
            metadata={
                "previous_tool": previous_tool,
                "current_tool": current_tool,
                "sequence_status": "VALID",
            },
        )


class ToolRateLimitRule(BaseRule):
    """Enforces rate limiting per tool per agent (e.g., Tool X called no more than N times per minute)."""

    def __init__(self, max_calls_per_minute: int = 20):
        self.max_calls_per_minute = max_calls_per_minute
        self._history: dict[str, list[float]] = defaultdict(list)

    @property
    def rule_id(self) -> str:
        return "RULE-SEC-RATE-LIMIT-007"

    @property
    def name(self) -> str:
        return "Tool Invocations Rate Limit Policy"

    @property
    def description(self) -> str:
        return f"Enforces that an agent calls Tool X no more than {self.max_calls_per_minute} times per minute."

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def priority(self) -> int:
        return 40

    @property
    def tags(self) -> list[str]:
        return ["rate-limit", "tool", "throttle"]

    @property
    def enabled(self) -> bool:
        return True

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> RuleResult:
        agent_key = f"{request.agent_id or 'default'}:{request.tool_name}"
        now = time.time()
        window = now - 60.0

        timestamps = [t for t in self._history[agent_key] if t > window]
        self._history[agent_key] = timestamps

        if len(timestamps) >= self.max_calls_per_minute:
            return RuleResult(
                matched=True,
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                risk_score=0.75,
                violation=f"Agent exceeded maximum allowed calls ({self.max_calls_per_minute}/min) for tool '{request.tool_name}'",
                recommendation="Throttle tool execution and return rate limit error",
                reason=f"Tool invocation count ({len(timestamps)}) exceeded rate limit window",
                metadata={"tool_name": request.tool_name, "recent_calls": len(timestamps)},
            )

        self._history[agent_key].append(now)
        return RuleResult(
            matched=False,
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=self.severity,
            risk_score=0.0,
            reason="Tool invocation rate within policy limits",
        )


class EmailSecurityRule(BaseRule):
    """Enforces email security policy validation including recipient syntax, domain allowlisting, and payload completeness."""

    _EMAIL_REGEX: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    @property
    def rule_id(self) -> str:
        return "RULE-SEC-EMAIL-008"

    @property
    def name(self) -> str:
        return "Email Security Policy"

    @property
    def description(self) -> str:
        return "Enforces recipient email format, domain allowlist, and non-empty subject/body requirements."

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def priority(self) -> int:
        return 40

    @property
    def stop_on_match(self) -> bool:
        return True

    @property
    def tags(self) -> list[str]:
        return ["email", "domain", "security", "validation"]

    @property
    def enabled(self) -> bool:
        return True

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> RuleResult:
        tool_name_lower = request.tool_name.lower().replace("_", "")
        if tool_name_lower not in ("sendemail", "email"):
            return RuleResult(
                matched=False,
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                risk_score=0.0,
                reason="Rule applies only to email dispatch tools",
            )

        params = request.parameters or {}
        recipient = str(params.get("recipient") or params.get("to") or params.get("email") or "").strip()
        subject = params.get("subject")
        body = params.get("body")

        # 1. Recipient syntax validation
        if not recipient or not self._EMAIL_REGEX.match(recipient):
            # Allow internal handles/aliases (e.g. 'manager', 'admin', 'team') by assuming default internal domain
            if "@" not in recipient:
                clean_alias = recipient.replace("_", "").replace("-", "")
                if clean_alias.isalnum():
                    domain = "enterprise.internal"
                    is_valid_format = True
                else:
                    domain = "unspecified"
                    is_valid_format = False
            else:
                is_valid_format = True
                domain = recipient.split("@")[-1].lower()

            if not is_valid_format:
                return RuleResult(
                    matched=True,
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    severity=self.severity,
                    risk_score=0.80,
                    violation=f"Recipient email '{recipient}' is not a valid email address format",
                    recommendation="Ensure recipient is formatted as a valid email address (e.g. user@domain.com)",
                    reason="Recipient must be a valid email address",
                    metadata={"recipient": recipient},
                )
        else:
            domain = recipient.split("@")[-1].lower()

        # 2. Domain allowlist validation
        settings = get_settings()
        allowed_domains = [d.lower() for d in settings.ALLOWED_EMAIL_DOMAINS if d]

        if allowed_domains and domain not in allowed_domains:
            return RuleResult(
                matched=True,
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                risk_score=0.80,
                violation=f"Recipient domain '{domain}' is not in allowed email domains: {allowed_domains}",
                recommendation=f"Restrict email dispatches to approved domain targets: {', '.join(allowed_domains)}",
                reason="Recipient domain not allowed",
                metadata={"recipient": recipient, "domain": domain, "allowed_domains": allowed_domains},
            )

        # 3. Payload completeness validation (if subject or body explicitly passed as empty strings)
        if subject is not None and str(subject).strip() == "":
            return RuleResult(
                matched=True,
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                risk_score=0.50,
                violation="Email subject line cannot be empty",
                recommendation="Provide a descriptive subject line for email notification",
                reason="Email subject cannot be empty",
            )

        if body is not None and str(body).strip() == "":
            return RuleResult(
                matched=True,
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                risk_score=0.50,
                violation="Email body content cannot be empty",
                recommendation="Provide non-empty body text for email notification",
                reason="Email body cannot be empty",
            )

        return RuleResult(
            matched=False,
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=self.severity,
            risk_score=0.0,
            reason="Email recipient, domain, and payload satisfy security policies",
        )


class CredentialSecurityRule(BaseRule):
    """Detects and blocks tool execution requests involving sensitive credentials, passwords, secrets, API keys, or private tokens."""

    _CREDENTIAL_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"\b(password|passwd|pwd)\b", re.IGNORECASE),
        re.compile(r"\b(api[-_]?key|apikey|secret[-_]?key|access[-_]?key)\b", re.IGNORECASE),
        re.compile(r"\b(bearer|auth[-_]?token|access[-_]?token|jwt|id[-_]?token)\b", re.IGNORECASE),
        re.compile(r"\b(private[-_]?key|ssh[-_]?key|id_rsa|id_ed25519|pem|pfx)\b", re.IGNORECASE),
        re.compile(r"\b(app[-_]?password|credentials?|db[-_]?pass|secret)\b", re.IGNORECASE),
        re.compile(r"(\.env|\benv[-_]?vars?|\benvironment[-_]?secrets?)\b", re.IGNORECASE),
    )

    @property
    def rule_id(self) -> str:
        return "RULE-SEC-CREDENTIAL-009"

    @property
    def name(self) -> str:
        return "Sensitive Credential & Secret Protection Policy"

    @property
    def description(self) -> str:
        return "Detects and prohibits requests or parameters involving passwords, API keys, secrets, tokens, or authentication credentials."

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.CRITICAL

    @property
    def priority(self) -> int:
        return 45

    @property
    def stop_on_match(self) -> bool:
        return True

    @property
    def tags(self) -> list[str]:
        return ["credential", "secret", "authentication", "protection"]

    @property
    def enabled(self) -> bool:
        return True

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> RuleResult:
        all_strings = _extract_all_strings(request.parameters)

        for text in all_strings:
            for pattern in self._CREDENTIAL_PATTERNS:
                if pattern.search(text):
                    matched_kw = pattern.pattern
                    return RuleResult(
                        matched=True,
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        severity=self.severity,
                        risk_score=0.95,
                        violation=f"Input parameter contains restricted authentication credential or secret pattern: '{matched_kw}'",
                        recommendation="Block execution and prevent exfiltration of sensitive credentials/keys",
                        reason="Tool invocation parameter contains restricted credential or secret data",
                        metadata={"matched_pattern": matched_kw},
                    )

        return RuleResult(
            matched=False,
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=self.severity,
            risk_score=0.0,
            reason="No sensitive credential or secret payloads detected",
        )


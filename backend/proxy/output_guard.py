"""Tool Output Guard for Agent WAF.

Intercepts, inspects, truncates, and sanitizes tool execution outputs
before feeding observations back into the LLM planner context window.

Protects against:
- Indirect Prompt Injection (IPI) embedded in tool outputs (files, emails, DB queries)
- Secret / Credential Leakage in tool observation results
- Buffer Overflow / Excessive Context Consumption from ultra-large tool outputs
"""

import json
import re
from typing import Any

from logger import get_logger
from tools.schemas import ToolResponse
from .sanitizer import redact_secrets

logger = get_logger(__name__)

# Max output length limit (characters) for tool observation results
DEFAULT_MAX_OUTPUT_LENGTH = 4000

# Regex patterns for matching Indirect Prompt Injection in tool outputs
_INDIRECT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+override", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"developer\s+(mode|message)", re.IGNORECASE),
    re.compile(r"reveal\s+(prompt|keys|credentials|secrets)", re.IGNORECASE),
    re.compile(r"override\s+(instructions|policy|policies|security|firewall)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(system|admin|root|jailbroken)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?prior", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"forget\s+(your|all|previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(allowed|authorized|permitted|a\s+new)", re.IGNORECASE),
)


class ToolOutputGuard:
    """Security guard inspecting and sanitizing tool execution output results."""

    def __init__(
        self,
        max_output_length: int = DEFAULT_MAX_OUTPUT_LENGTH,
        enable_injection_scrubbing: bool = True,
        enable_secret_redaction: bool = True,
    ) -> None:
        self.max_output_length = max_output_length
        self.enable_injection_scrubbing = enable_injection_scrubbing
        self.enable_secret_redaction = enable_secret_redaction

    def sanitize_output(self, raw_output: Any) -> tuple[Any, dict[str, Any]]:
        """Sanitize raw tool output: redact secrets, scrub prompt injections, and truncate length.

        Returns tuple of (sanitized_output, guard_metadata).
        """
        guard_metadata: dict[str, Any] = {
            "output_guard_applied": True,
            "truncated": False,
            "prompt_injection_detected": False,
            "secrets_redacted": False,
        }

        if raw_output is None:
            return None, guard_metadata

        # Convert non-string outputs to JSON string representation if dict/list
        if isinstance(raw_output, (dict, list)):
            output_str = json.dumps(raw_output, indent=2)
            is_json_obj = True
        else:
            output_str = str(raw_output)
            is_json_obj = False

        # 1. Secret Redaction
        if self.enable_secret_redaction:
            redacted_str = redact_secrets(output_str)
            if redacted_str != output_str:
                guard_metadata["secrets_redacted"] = True
                logger.warning("ToolOutputGuard redacted credentials from tool output")
            output_str = redacted_str

        # 2. Indirect Prompt Injection Scrubbing
        if self.enable_injection_scrubbing:
            injection_found = False
            for pattern in _INDIRECT_INJECTION_PATTERNS:
                if pattern.search(output_str):
                    injection_found = True
                    output_str = pattern.sub("[REDACTED_INDIRECT_PROMPT_INJECTION]", output_str)

            if injection_found:
                guard_metadata["prompt_injection_detected"] = True
                logger.warning("ToolOutputGuard detected and scrubbed Indirect Prompt Injection from tool output")
                output_str = (
                    "[AGENT WAF SECURITY GUARD: Suspicious prompt injection payload detected & scrubbed from tool output]\n"
                    + output_str
                )

        # 3. Output Truncation
        if len(output_str) > self.max_output_length:
            guard_metadata["truncated"] = True
            guard_metadata["original_length"] = len(output_str)
            guard_metadata["truncated_length"] = self.max_output_length
            output_str = (
                output_str[: self.max_output_length]
                + f"\n... [Output Truncated by Agent WAF Output Guard (Max {self.max_output_length} chars)]"
            )
            logger.info("ToolOutputGuard truncated tool output", extra={"original_len": guard_metadata["original_length"]})

        # Re-parse JSON if original output was object and not scrubbed into raw header text
        final_output: Any = output_str
        if is_json_obj and not guard_metadata["prompt_injection_detected"] and not guard_metadata["truncated"]:
            try:
                final_output = json.loads(output_str)
            except Exception:
                final_output = output_str

        return final_output, guard_metadata

    def inspect_and_sanitize_response(self, response: ToolResponse) -> ToolResponse:
        """Inspect and sanitize ToolResponse object in-place or return copy."""
        if not response.success or response.result is None:
            return response

        sanitized_result, metadata = self.sanitize_output(response.result)

        # Merge metadata
        merged_metadata = response.metadata.copy() if response.metadata else {}
        merged_metadata.update(metadata)

        return ToolResponse(
            success=response.success,
            result=sanitized_result,
            error=response.error,
            execution_time_ms=response.execution_time_ms,
            metadata=merged_metadata,
        )

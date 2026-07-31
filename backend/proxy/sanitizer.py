"""Secret Redactor and Sanitizer for Agent WAF.

Redacts API keys, JWTs, Bearer tokens, passwords, and sensitive credentials
from parameters, observations, and audit log payloads before logging or publishing.
"""

import re
from typing import Any

# Regex patterns for matching sensitive credentials and secrets
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    # API Keys (OpenAI, Groq, Anthropic, Generic)
    re.compile(r"\b(sk-[a-zA-Z0-9_-]{20,})\b"),
    re.compile(r"\b(gsk_[a-zA-Z0-9_-]{20,})\b"),
    re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
    # JWT Tokens
    re.compile(r"\b(eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]+)\b"),
    # Bearer Tokens
    re.compile(r"Bearer\s+([a-zA-Z0-9_\-\.=]{16,})", re.IGNORECASE),
    # Key-Value assignments: api_key=..., password=..., token=...
    re.compile(
        r"(?i)\b(api_?key|password|passwd|secret|auth_?token|access_?token|private_?key)\s*[:=]\s*['\"]?([^\s'\";&]+)['\"]?"
    ),
)

_SENSITIVE_KEY_NAMES: set[str] = {
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "token",
    "auth_token",
    "access_token",
    "private_key",
    "credentials",
    "authorization",
}


def redact_secrets_text(text: str) -> str:
    """Redact secret patterns (API keys, JWTs, passwords, Bearer tokens) from a raw text string."""
    if not isinstance(text, str) or not text:
        return text

    sanitized = text

    # Redact explicit regex patterns
    # 1. API Keys (sk-..., gsk-..., AKIA...)
    sanitized = re.sub(r"\b(sk-[a-zA-Z0-9_-]{20,})\b", "[REDACTED_API_KEY]", sanitized)
    sanitized = re.sub(r"\b(gsk_[a-zA-Z0-9_-]{20,})\b", "[REDACTED_GROQ_KEY]", sanitized)
    sanitized = re.sub(r"\b(AKIA[0-9A-Z]{16})\b", "[REDACTED_AWS_KEY]", sanitized)

    # 2. JWT Tokens
    sanitized = re.sub(
        r"\b(eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]+)\b",
        "[REDACTED_JWT_TOKEN]",
        sanitized,
    )

    # 3. Bearer Tokens
    sanitized = re.sub(
        r"(?i)Bearer\s+[a-zA-Z0-9_\-\.=]{16,}",
        "Bearer [REDACTED_BEARER_TOKEN]",
        sanitized,
    )

    # 4. Key-Value secrets (e.g. password=xyz, api_key: "abc123456789")
    def _kv_replacer(match: re.Match[str]) -> str:
        key_name = match.group(1)
        return f"{key_name}=[REDACTED_SECRET]"

    sanitized = re.sub(
        r"(?i)\b(api_?key|password|passwd|secret|auth_?token|access_?token|private_?key)\s*[:=]\s*['\"]?[^\s'\";&]+['\"]?",
        _kv_replacer,
        sanitized,
    )

    return sanitized


def redact_secrets(data: Any) -> Any:
    """Recursively redact secrets across dictionary parameters, lists, or string values."""
    if isinstance(data, str):
        return redact_secrets_text(data)

    elif isinstance(data, dict):
        sanitized_dict: dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(k, str) and any(sens in k.lower() for sens in _SENSITIVE_KEY_NAMES):
                sanitized_dict[k] = "[REDACTED_SECRET]"
            else:
                sanitized_dict[k] = redact_secrets(v)
        return sanitized_dict

    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]

    elif isinstance(data, tuple):
        return tuple(redact_secrets(item) for item in data)

    return data

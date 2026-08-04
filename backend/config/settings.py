from functools import lru_cache
import json
from typing import Any, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings for Agent WAF built with Pydantic v2.
    
    Loads configuration settings from environment variables and .env files.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=True,
    )

    # Application Configuration
    APP_NAME: str = "Agent WAF"
    APP_DESCRIPTION: str = "Enterprise-grade Agent Web Application Firewall"
    APP_VERSION: str = "1.0.0"
    AGENT_ID: str = "langgraph_agent_v1"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False

    # WAF Operating Mode: ENFORCE (Active blocking) | SHADOW (Log & monitor only)
    WAF_MODE: Literal["ENFORCE", "SHADOW"] = "ENFORCE"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./agent_waf.db"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Logging Configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"

    # Security Configuration
    CORS_ORIGINS: Any = ["http://localhost:3000", "http://localhost:8000"]

    # WAF Engine & Security Policy Configuration
    SHADOW_MODE: bool = False
    REQUEST_TIMEOUT: int = Field(default=30, ge=1, le=300)
    RATE_LIMIT_WINDOW: int = Field(default=60, ge=1)
    DEFAULT_RISK_THRESHOLD: float = Field(default=0.5, ge=0.0, le=1.0)
    MAX_PARAMETER_LENGTH: int = Field(default=5000, ge=1)
    MAX_PARAMETER_DEPTH: int = Field(default=5, ge=1)
    PROMPT_INJECTION_ENABLED: bool = True
    SQL_INJECTION_ENABLED: bool = True
    DANGEROUS_TOOL_ENABLED: bool = True
    PARAMETER_SIZE_ENABLED: bool = True
    DENIED_TOOL_CATEGORIES: list[str] = ["filesystem", "shell", "terminal", "system"]
    GROQ_API_KEY: str | None = Field(default=None, description="Groq LLM API Key")
    GROQ_PLANNER_MODELS: Any = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
    PERMITTED_DATA_SCOPES: list[str] = ["customer_123", "doc_99", "project_alpha", "dataset_public", "project_report"]

    # Gmail SMTP & Email Security Configuration
    GMAIL_EMAIL: str = ""
    GMAIL_APP_PASSWORD: str = ""
    ALLOWED_EMAIL_DOMAINS: Any = ["gmail.com", "company.com", "enterprise.internal", "example.com"]

    @property
    def RISK_THRESHOLD(self) -> float:
        """Alias property for DEFAULT_RISK_THRESHOLD."""
        return self.DEFAULT_RISK_THRESHOLD

    @property
    def is_shadow_mode(self) -> bool:
        """Check if WAF is operating in SHADOW mode (either WAF_MODE='SHADOW' or SHADOW_MODE=True)."""
        return self.WAF_MODE == "SHADOW" or self.SHADOW_MODE

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, v: Any) -> str:
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("development", "staging", "production", "test"):
                return v_lower
        return "production"

    @field_validator("WAF_MODE", mode="before")
    @classmethod
    def normalize_waf_mode(cls, v: Any) -> str:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ("ENFORCE", "SHADOW"):
                return v_upper
        return "ENFORCE"

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, v: Any) -> str:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
                return v_upper
        return "INFO"

    @field_validator("LOG_FORMAT", mode="before")
    @classmethod
    def normalize_log_format(cls, v: Any) -> str:
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("json", "text"):
                return v_lower
        return "json"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: Any) -> str:
        """Validate and convert database URLs for SQLAlchemy asyncpg engines (e.g. Neon Postgres)."""
        if isinstance(v, str):
            v = v.strip()
            # Clean query parameters for asyncpg engine driver
            v = v.replace("&channel_binding=require", "").replace("?channel_binding=require&", "?").replace("?channel_binding=require", "")
            v = v.replace("sslmode=require", "ssl=require").replace("sslmode=prefer", "ssl=prefer").replace("sslmode=disable", "ssl=disable")
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return str(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """Validate and parse CORS_ORIGINS from wildcard '*', JSON string, or CSV format."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v == "*" or v == '"*"' or v == "'*'":
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(origin) for origin in v]
        return ["*"]

    @field_validator("ALLOWED_EMAIL_DOMAINS", mode="before")
    @classmethod
    def assemble_allowed_email_domains(cls, v: Any) -> list[str]:
        """Validate and parse ALLOWED_EMAIL_DOMAINS from CSV or JSON list."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [dom.strip().lower() for dom in v.split(",") if dom.strip()]
        elif isinstance(v, list):
            return [str(dom).strip().lower() for dom in v]
        return ["gmail.com", "company.com", "enterprise.internal", "example.com"]

    @property
    def is_development(self) -> bool:
        """Check if application is running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if application is running in production mode."""
        return self.ENVIRONMENT == "production"

    @property
    def is_staging(self) -> bool:
        """Check if application is running in staging mode."""
        return self.ENVIRONMENT == "staging"

    @property
    def is_test(self) -> bool:
        """Check if application is running in test mode."""
        return self.ENVIRONMENT == "test"

    @property
    def is_debug(self) -> bool:
        """Check if debug mode is active."""
        return self.DEBUG


@lru_cache
def get_settings() -> Settings:
    """Return a cached single instance of application settings.
    
    Uses @lru_cache to guarantee a singleton instance throughout application execution.
    """
    return Settings()

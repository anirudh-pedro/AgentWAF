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
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False

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
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Future WAF Configuration
    SHADOW_MODE: bool = False
    REQUEST_TIMEOUT: int = Field(default=30, ge=1, le=300)
    RATE_LIMIT_WINDOW: int = Field(default=60, ge=1)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """Validate and parse CORS_ORIGINS from wildcard '*', JSON string, or CSV format."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v == "*":
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON array string for CORS_ORIGINS: {v}")
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(origin) for origin in v]
        raise ValueError(f"Invalid format for CORS_ORIGINS: {v}")

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

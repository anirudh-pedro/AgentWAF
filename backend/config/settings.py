from functools import lru_cache
import json
from typing import Any, Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings validated with Pydantic v2.
    
    Reads from environment variables and optional .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application Meta
    APP_NAME: str = "Agent WAF"
    APP_VERSION: str = "1.0.0"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Middleware & Request Tracing
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security & CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./agent_waf.db"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Logging Configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """Validate and normalize CORS origins input from environment variable."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON format for CORS_ORIGINS: {v}")
            return [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            return [str(item) for item in v]
        raise ValueError(f"Invalid CORS_ORIGINS format: {v}")

    @property
    def is_production(self) -> bool:
        """Helper check if running in production mode."""
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    """Singleton getter for application settings with LRU caching."""
    return Settings()


# Export explicit singleton instance for convenience
settings: Settings = get_settings()

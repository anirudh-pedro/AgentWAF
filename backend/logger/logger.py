import json
import logging
import sys
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from config import get_settings

# Lock for thread-safe LoggerManager singleton initialization
_lock = Lock()

# Third-party loggers and their configured suppression levels
_THIRD_PARTY_LOGGERS: dict[str, int] = {
    "uvicorn": logging.INFO,
    "uvicorn.access": logging.WARNING,
    "sqlalchemy.engine": logging.WARNING,
}

# Reserved attributes on logging.LogRecord to ignore when extracting extra attributes
_RESERVED_LOG_RECORD_FIELDS: set[str] = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for CloudWatch, OpenTelemetry, and log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        # Format exact event creation time in UTC with ISO-8601 Z format
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        timestamp_str = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        log_data: dict[str, Any] = {
            "timestamp": timestamp_str,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "log_process": record.process,
            "log_thread": record.threadName,
        }

        # Include tracing and security context placeholders if present
        for field in ("request_id", "agent_id", "session_id", "tool_name"):
            val = getattr(record, field, None)
            if val is not None:
                log_data[field] = val

        # Include exception traceback if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include stack info if present
        if record.stack_info:
            log_data["stack"] = record.stack_info

        # Include arbitrary extra key-value attributes passed in logger calls
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_FIELDS and key not in log_data:
                log_data[key] = value

        return json.dumps(log_data, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for local development console log inspection."""

    DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self.DEFAULT_FORMAT, datefmt=self.DATE_FORMAT)

    def format(self, record: logging.LogRecord) -> str:
        res = super().format(record)
        request_id = getattr(record, "request_id", None)
        if request_id:
            res = f"{res} [request_id={request_id}]"
        return res


class LoggerManager:
    """Thread-safe manager encapsulating root logger configuration and third-party logger tuning."""

    _instance: "LoggerManager | None" = None

    def __init__(self) -> None:
        self.settings = get_settings()
        self._configure_root_logger()
        self._configure_third_party_loggers()

    @classmethod
    def get_instance(cls) -> "LoggerManager":
        """Get or initialize singleton instance of LoggerManager using double-checked locking."""
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _configure_root_logger(self) -> None:
        """Initialize the primary agent_waf parent logger and handler idempotently."""
        root_logger = logging.getLogger("agent_waf")
        log_level = getattr(logging, self.settings.LOG_LEVEL.upper(), logging.INFO)
        root_logger.setLevel(log_level)
        root_logger.propagate = False

        if not root_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(log_level)

            if self.settings.LOG_FORMAT == "json":
                handler.setFormatter(JSONFormatter())
            else:
                handler.setFormatter(TextFormatter())

            root_logger.addHandler(handler)

    def _configure_third_party_loggers(self) -> None:
        """Suppress noise from verbose framework loggers based on _THIRD_PARTY_LOGGERS mapping."""
        for logger_name, level in _THIRD_PARTY_LOGGERS.items():
            logging.getLogger(logger_name).setLevel(level)

    def get_logger(self, name: str) -> logging.Logger:
        """Return namespaced logger within agent_waf hierarchy."""
        if name == "agent_waf" or name.startswith("agent_waf."):
            return logging.getLogger(name)
        return logging.getLogger(f"agent_waf.{name}")


def get_logger(name: str) -> logging.Logger:
    """Retrieve a configured logger instance namespaced within the agent_waf hierarchy.
    
    Args:
        name: The component or module name (__name__).
        
    Returns:
        A logging.Logger configured with structured formatters and safe stream handlers.
    """
    manager = LoggerManager.get_instance()
    return manager.get_logger(name)

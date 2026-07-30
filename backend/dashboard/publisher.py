from threading import Lock
from typing import Callable

from logger import get_logger
from .models import AuditEvent

logger = get_logger(__name__)

_lock = Lock()


class AuditEventPublisher:
    """Decoupled Event Publisher managing subscriber listeners for audit events."""

    _instance: "AuditEventPublisher | None" = None

    def __init__(self) -> None:
        self._subscribers: list[Callable[[AuditEvent], None]] = []

    @classmethod
    def get_instance(cls) -> "AuditEventPublisher":
        """Thread-safe singleton accessor for AuditEventPublisher."""
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def subscribe(self, callback: Callable[[AuditEvent], None]) -> None:
        """Register a subscriber callback listener for audit events."""
        with _lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def publish(self, event: AuditEvent) -> None:
        """Publish an audit event to all registered subscriber listeners."""
        with _lock:
            subscribers = list(self._subscribers)

        for callback in subscribers:
            try:
                callback(event)
            except Exception as exc:
                logger.warning("Error in audit event subscriber callback", extra={"error": str(exc)})

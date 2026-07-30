from abc import ABC, abstractmethod
import time
from typing import Any

from .schemas import ToolRequest, ToolResponse


class BaseTool(ABC):
    """Abstract base class that all Agent WAF tools must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        pass

    @property
    def version(self) -> str:
        """Version string of the tool implementation."""
        return "1.0.0"

    @abstractmethod
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute tool logic asynchronously for the given request."""
        pass

    def create_success_response(
        self,
        result: Any,
        start_time: float,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResponse:
        """Helper to build a successful ToolResponse with automatic duration timing."""
        duration_ms = (time.perf_counter() - start_time) * 1000
        return ToolResponse(
            success=True,
            result=result,
            error=None,
            execution_time_ms=duration_ms,
            metadata=metadata or {},
        )

    def create_error_response(
        self,
        error_message: str,
        start_time: float,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResponse:
        """Helper to build an error ToolResponse with automatic duration timing."""
        duration_ms = (time.perf_counter() - start_time) * 1000
        return ToolResponse(
            success=False,
            result=None,
            error=error_message,
            execution_time_ms=duration_ms,
            metadata=metadata or {},
        )

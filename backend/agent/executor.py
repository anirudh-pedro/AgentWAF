import time
import uuid
from typing import Any

from config import get_settings
from logger import get_logger
from tools import ToolRegistry, ToolRequest, ToolResponse

logger = get_logger(__name__)


class ToolRequestFactory:
    """Factory for constructing enriched ToolRequest objects across agent lifecycles."""

    @staticmethod
    def create(
        tool_name: str,
        parameters: dict[str, Any],
        request_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ToolRequest:
        settings = get_settings()
        return ToolRequest(
            tool_name=tool_name,
            parameters=parameters,
            request_id=request_id or str(uuid.uuid4()),
            agent_id=agent_id or settings.AGENT_ID,
            session_id=session_id,
            metadata=metadata or {},
        )


class AgentToolExecutor:
    """Decoupled executor responsible for discovering and dispatching ToolRequests to registered tools."""

    def __init__(self) -> None:
        self.registry = ToolRegistry.get_instance()

    def discover_tools(self) -> list[dict[str, Any]]:
        """Dynamically discover metadata for all tools currently registered in the ToolRegistry."""
        tools = self.registry.list_tools()
        logger.debug(
            "Discovered registered tools for agent runtime",
            extra={"count": len(tools), "tools": [t["name"] for t in tools]}
        )
        return tools

    async def execute_tool(self, request: ToolRequest) -> ToolResponse:
        """Execute a ToolRequest against the registered tool implementation.
        
        Guarantees exception safety: returns a structured ToolResponse error if execution or lookup fails.
        """
        start_time = time.perf_counter()
        logger.info(
            "Agent ToolExecutor dispatching tool request",
            extra={
                "tool_name": request.tool_name,
                "request_id": request.request_id,
                "agent_id": request.agent_id,
            }
        )

        try:
            tool = self.registry.get(request.tool_name)
            response = await tool.execute(request)

            logger.info(
                "Agent ToolExecutor completed tool execution",
                extra={
                    "tool_name": request.tool_name,
                    "success": response.success,
                    "execution_time_ms": response.execution_time_ms,
                    "request_id": request.request_id,
                }
            )
            return response

        except KeyError:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(
                "Tool lookup failed in Agent ToolExecutor",
                extra={"tool_name": request.tool_name, "request_id": request.request_id}
            )
            return ToolResponse(
                success=False,
                result=None,
                error=f"Tool '{request.tool_name}' is not registered in ToolRegistry",
                execution_time_ms=duration_ms,
                metadata={"error_type": "missing_tool"},
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Unhandled error executing tool in Agent ToolExecutor",
                extra={"tool_name": request.tool_name, "request_id": request.request_id}
            )
            return ToolResponse(
                success=False,
                result=None,
                error=f"Tool execution failed: {str(exc)}",
                execution_time_ms=duration_ms,
                metadata={"error_type": "tool_exception"},
            )

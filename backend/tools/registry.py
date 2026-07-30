from threading import Lock
from typing import Any

from logger import get_logger
from .base import BaseTool

logger = get_logger(__name__)

_lock = Lock()


class ToolRegistry:
    """Thread-safe registry for agent tools with O(1) lookup capabilities."""

    _instance: "ToolRegistry | None" = None

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        """Thread-safe singleton accessor for ToolRegistry."""
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance into the registry.
        
        Raises:
            ValueError: If tool argument is invalid or duplicate tool name is registered.
        """
        if not isinstance(tool, BaseTool):
            raise ValueError(f"Object {tool} is not an instance of BaseTool")

        tool_name = tool.name.strip()
        if not tool_name:
            raise ValueError("Tool name cannot be empty")

        with _lock:
            if tool_name in self._tools:
                logger.warning(
                    "Attempted to register duplicate tool",
                    extra={"tool_name": tool_name}
                )
                raise ValueError(f"Tool with name '{tool_name}' is already registered")

            self._tools[tool_name] = tool
            logger.info(
                "Registered agent tool successfully",
                extra={"tool_name": tool_name, "version": tool.version}
            )

    def unregister(self, name: str) -> None:
        """Unregister a tool by name.
        
        Raises:
            KeyError: If tool name is not present in registry.
        """
        tool_name = name.strip()
        with _lock:
            if tool_name not in self._tools:
                raise KeyError(f"Tool '{tool_name}' is not registered")

            del self._tools[tool_name]
            logger.info("Unregistered agent tool", extra={"tool_name": tool_name})

    def get(self, name: str) -> BaseTool:
        """Retrieve a registered tool by name with O(1) lookup.
        
        Raises:
            KeyError: If tool name is not registered.
        """
        tool_name = name.strip()
        with _lock:
            tool = self._tools.get(tool_name)
            if tool is None:
                logger.warning("Tool lookup failed", extra={"tool_name": tool_name})
                raise KeyError(f"Tool '{tool_name}' is not registered in registry")
            return tool

    def list_tools(self) -> list[dict[str, Any]]:
        """Return a list of metadata for all registered tools."""
        with _lock:
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "version": tool.version,
                }
                for tool in self._tools.values()
            ]

    def clear(self) -> None:
        """Clear all registered tools (useful for unit test isolation)."""
        with _lock:
            self._tools.clear()
            logger.debug("Cleared all tool registrations")

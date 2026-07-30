from logger import get_logger
from .base import BaseTool
from .implementations import CalculatorTool, DateTimeTool, EchoTool
from .registry import ToolRegistry

logger = get_logger(__name__)

# Class tuple of built-in tool implementations to instantiate and register
_BUILTIN_TOOL_CLASSES: tuple[type[BaseTool], ...] = (
    EchoTool,
    CalculatorTool,
    DateTimeTool,
)


def register_builtin_tools() -> None:
    """Instantiate and register all built-in agent tools into the ToolRegistry.
    
    Safe to execute multiple times during application lifecycle without throwing duplicate registration errors.
    """
    registry = ToolRegistry.get_instance()
    registered_names: list[str] = []

    for tool_cls in _BUILTIN_TOOL_CLASSES:
        tool_instance = tool_cls()
        try:
            registry.register(tool_instance)
            registered_names.append(tool_instance.name)
        except ValueError as exc:
            logger.debug(
                "Skipping tool registration (already registered)",
                extra={"tool_name": tool_instance.name, "reason": str(exc)}
            )

    if registered_names:
        logger.info(
            "Built-in agent tools registered successfully",
            extra={"tools": registered_names, "total_registered": len(registered_names)}
        )

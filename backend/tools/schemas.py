from typing import Any
from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    """Pydantic schema representing a structured request to execute an agent tool."""

    tool_name: str = Field(..., description="Name of the target tool to execute")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Input arguments for the tool")
    request_id: str | None = Field(default=None, description="Correlation request ID for tracing")
    agent_id: str | None = Field(default=None, description="Identifier of the calling AI agent")
    session_id: str | None = Field(default=None, description="Session identifier for multi-turn agent interactions")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")


class ToolResponse(BaseModel):
    """Pydantic schema representing the structured execution result of an agent tool."""

    success: bool = Field(..., description="Flag indicating whether execution succeeded")
    result: Any = Field(default=None, description="Output payload produced by the tool")
    error: str | None = Field(default=None, description="Error message if execution failed")
    execution_time_ms: float = Field(default=0.0, description="Tool execution duration in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Execution metadata for auditing and security inspect")

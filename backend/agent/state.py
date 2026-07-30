from typing import Annotated, Any, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from tools.schemas import ToolRequest, ToolResponse


class AgentState(TypedDict):
    """Strongly typed LangGraph state schema for Agent WAF execution lifecycle."""

    # Conversation message history
    messages: Annotated[list[BaseMessage], add_messages]

    # Tool invocation request payload
    tool_request: ToolRequest | None

    # Tool execution result payload
    tool_response: ToolResponse | None

    # Name of the currently selected tool
    selected_tool: str | None

    # Additional execution metadata
    execution_metadata: dict[str, Any]

    # Placeholders for Module 10 Agent WAF Proxy inspection
    policy_result: str | None
    risk_score: float | None
    blocked: bool | None

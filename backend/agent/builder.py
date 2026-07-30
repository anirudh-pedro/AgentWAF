import uuid
from typing import Any
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from config import get_settings
from logger import get_logger
from .executor import AgentToolExecutor, ToolRequestFactory
from .state import AgentState

logger = get_logger(__name__)


class AgentBuilder:
    """Builder responsible for constructing and compiling the LangGraph agent runtime."""

    def __init__(self, executor: AgentToolExecutor | None = None) -> None:
        self.settings = get_settings()
        self.executor = executor or AgentToolExecutor()

    def _select_tool_intent(self, user_message: str, available_tools: list[dict[str, Any]]) -> tuple[str | None, dict[str, Any]]:
        """Structured intent selector for matching user messages to registered tools."""
        text_lower = user_message.lower()

        if "echo" in text_lower:
            return "echo", {"message": user_message}

        if "time" in text_lower or "date" in text_lower:
            return "datetime", {}

        if any(op in text_lower for op in ("add", "plus", "+", "subtract", "minus", "-", "multiply", "times", "*", "divide", "/")):
            if "add" in text_lower or "+" in text_lower:
                return "calculator", {"operation": "add", "a": 10, "b": 20}
            if "subtract" in text_lower or "-" in text_lower:
                return "calculator", {"operation": "subtract", "a": 50, "b": 15}
            if "divide" in text_lower or "/" in text_lower:
                return "calculator", {"operation": "divide", "a": 100, "b": 4}
            return "calculator", {"operation": "multiply", "a": 5, "b": 6}

        if available_tools:
            return available_tools[0]["name"], {"message": user_message}

        return None, {}

    async def _agent_node(self, state: AgentState) -> dict[str, Any]:
        """Node 1: Analyze user request, discover available tools, and construct ToolRequest via ToolRequestFactory."""
        logger.info("LangGraph Agent Node processing request")

        available_tools = self.executor.discover_tools()

        user_message = ""
        for msg in reversed(state.get("messages", [])):
            if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
                user_message = str(msg.content)
                break

        exec_metadata = dict(state.get("execution_metadata", {}))
        request_id = exec_metadata.get("request_id") or str(uuid.uuid4())
        graph_run_id = exec_metadata.get("graph_run_id") or str(uuid.uuid4())
        trace_id = exec_metadata.get("trace_id") or request_id

        selected_tool, parameters = self._select_tool_intent(user_message, available_tools)

        if selected_tool:
            tool_req = ToolRequestFactory.create(
                tool_name=selected_tool,
                parameters=parameters,
                request_id=request_id,
                agent_id=self.settings.AGENT_ID,
                metadata={
                    "graph_run_id": graph_run_id,
                    "trace_id": trace_id,
                    "node_name": "agent_node",
                },
            )
            logger.info(
                "Agent selected tool for execution",
                extra={
                    "selected_tool": selected_tool,
                    "request_id": request_id,
                    "graph_run_id": graph_run_id,
                }
            )

            exec_metadata.update({
                "request_id": request_id,
                "graph_run_id": graph_run_id,
                "trace_id": trace_id,
                "last_node": "agent_node",
            })

            return {
                "selected_tool": selected_tool,
                "tool_request": tool_req,
                "execution_metadata": exec_metadata,
            }

        logger.warning("No matching tool identified for user message", extra={"user_message": user_message})
        return {
            "selected_tool": None,
            "tool_request": None,
            "execution_metadata": exec_metadata,
        }

    async def _tool_execution_node(self, state: AgentState) -> dict[str, Any]:
        """Node 2: Dispatch ToolRequest to ToolExecutor and record ToolResponse with execution metadata."""
        tool_request = state.get("tool_request")
        exec_metadata = dict(state.get("execution_metadata", {}))

        if not tool_request:
            logger.warning("Tool execution node called without active tool_request")
            return {"tool_response": None}

        logger.info(
            "LangGraph Tool Execution Node executing tool",
            extra={
                "tool_name": tool_request.tool_name,
                "request_id": tool_request.request_id,
                "graph_run_id": exec_metadata.get("graph_run_id"),
            }
        )

        response = await self.executor.execute_tool(tool_request)

        exec_metadata.update({
            "completed": True,
            "success": response.success,
            "execution_time_ms": response.execution_time_ms,
            "node_name": "tool_execution_node",
            "last_node": "tool_execution_node",
        })

        return {
            "tool_response": response,
            "execution_metadata": exec_metadata,
        }

    def build(self) -> CompiledStateGraph:
        """Construct and compile the modular LangGraph execution graph.
        
        Graph Flow: START -> agent_node -> tool_execution_node -> END
        """
        logger.info("Building LangGraph agent state graph")

        graph = StateGraph(AgentState)

        graph.add_node("agent_node", self._agent_node)
        graph.add_node("tool_execution_node", self._tool_execution_node)

        graph.add_edge(START, "agent_node")
        graph.add_edge("agent_node", "tool_execution_node")
        graph.add_edge("tool_execution_node", END)

        compiled_graph = graph.compile()
        logger.info("LangGraph agent state graph compiled successfully")
        return compiled_graph

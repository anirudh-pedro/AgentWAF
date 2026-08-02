import re
import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from agent.executor import AgentToolExecutor
from agent.workflow_executor import WorkflowExecutor
from logger import get_logger
from proxy.proxy import AgentWAFProxy
from rules.engine import RuleEngine, RuleEnginePolicyEvaluator
from tools.loader import register_builtin_tools
from tools.registry import ToolRegistry
from tools.schemas import ToolRequest

logger = get_logger(__name__)

router = APIRouter(prefix="/agent", tags=["Agent Execution & WAF Proxy Inspection"])


class UserQueryRequest(BaseModel):
    tool_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Target tool to invoke (e.g., echo, calculator, datetime)",
    )
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User prompt or parameter input for WAF inspection (max 10,000 chars)",
    )
    parameters: dict[str, Any] | None = Field(default=None, description="Optional tool parameters dict")


class UserQueryResponse(BaseModel):
    request_id: str
    tool_name: str
    policy_result: str
    risk_score: float
    matched_rules: list[str]
    violations: list[str]
    reason: str | None = None
    output: Any | None = None
    execution_time_ms: float


class AgentRunRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=5000, description="Natural language user goal or prompt")
    session_id: str | None = Field(default=None, description="Optional session ID for stateful tracking")


class AgentRunStep(BaseModel):
    step_index: int
    tool: str
    parameters: dict[str, Any]
    status: str
    risk: float
    matched_rules: list[str]
    violations: list[str]
    reason: str | None = None
    thought: str | None = None
    output: Any | None = None
    execution_time_ms: float


class AgentRunResponse(BaseModel):
    workflow: str
    goal: str
    status: str
    session_id: str
    total_steps: int
    steps: list[AgentRunStep]
    blocked_info: AgentRunStep | None = None
    final_response: str
    total_execution_time_ms: float


_proxy_instance: AgentWAFProxy | None = None


def get_waf_proxy() -> AgentWAFProxy:
    global _proxy_instance
    if _proxy_instance is None:
        register_builtin_tools()
        rule_engine = RuleEngine.get_instance()
        inner_executor = AgentToolExecutor()
        policy_evaluator = RuleEnginePolicyEvaluator(engine=rule_engine)
        _proxy_instance = AgentWAFProxy(inner_executor=inner_executor, evaluator=policy_evaluator)
    return _proxy_instance


def parse_calculator_params(prompt: str) -> dict[str, Any]:
    """Parse user natural language or math prompt into calculator tool parameters ('operation', 'a', 'b')."""
    text = prompt.lower()
    
    # Detect operation
    op = "add"
    if "sub" in text or "minus" in text or "-" in text:
        op = "subtract"
    elif "mul" in text or "times" in text or "*" in text or "product" in text:
        op = "multiply"
    elif "div" in text or "/" in text or "over" in text:
        op = "divide"
    elif "add" in text or "plus" in text or "sum" in text or "+" in text:
        op = "add"

    # Extract numeric operands
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    num_a = numbers[0] if len(numbers) > 0 else "0"
    num_b = numbers[1] if len(numbers) > 1 else "0"

    return {"operation": op, "a": num_a, "b": num_b}


@router.post(
    "/execute",
    response_model=UserQueryResponse,
    summary="Execute Single Agent Request Through WAF Inspection Proxy",
    description="Inspects user prompt against Agent WAF security rules and executes tool if policy decision is ALLOW.",
)
async def execute_agent_query(payload: UserQueryRequest) -> UserQueryResponse:
    """Submit a prompt/tool request to Agent WAF for inspection and policy-enforced execution."""
    logger.info(
        "Agent WAF Query API request received",
        extra={"tool_name": payload.tool_name, "prompt_length": len(payload.prompt)},
    )

    try:
        waf_proxy = get_waf_proxy()
        req_id = f"req-{uuid.uuid4().hex[:8]}"

        # Construct parameter payload based on tool_name
        params: dict[str, Any] = payload.parameters or {}
        if not params:
            if payload.tool_name == "echo":
                params = {"message": payload.prompt}
            elif payload.tool_name == "calculator":
                params = parse_calculator_params(payload.prompt)
            elif payload.tool_name == "datetime":
                params = {"action": "current_time"}
            else:
                params = {"message": payload.prompt, "query": payload.prompt, "command": payload.prompt}

        tool_req = ToolRequest(
            tool_name=payload.tool_name,
            parameters=params,
            request_id=req_id,
            metadata={"goal": payload.prompt, "prompt": payload.prompt},
        )

        tool_resp = await waf_proxy.execute_tool(tool_req)

        meta = tool_resp.metadata or {}
        policy_res = meta.get("policy_result") or ("ALLOW" if tool_resp.success else "BLOCK")
        risk_sc = float(meta.get("risk_score", 0.0))
        matched_rls = meta.get("matched_rules", [])
        violation_list = meta.get("violations", [])
        reason_str = meta.get("reason") or tool_resp.error

        is_allowed = policy_res in ("ALLOW", "SHADOW_BLOCK")
        output_data = tool_resp.result if (is_allowed and tool_resp.success) else ({"error": tool_resp.error} if is_allowed else None)

        return UserQueryResponse(
            request_id=req_id,
            tool_name=payload.tool_name,
            policy_result=policy_res,
            risk_score=risk_sc,
            matched_rules=matched_rls,
            violations=violation_list,
            reason=reason_str if not is_allowed else None,
            output=output_data,
            execution_time_ms=tool_resp.execution_time_ms,
        )

    except Exception as exc:
        logger.exception("Failed to execute agent query through WAF proxy", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"WAF Proxy inspection failed: {str(exc)}",
        ) from exc


@router.post(
    "/run",
    response_model=AgentRunResponse,
    summary="Run AI Agent Goal Through ReAct Reasoning Loop & WAF Proxy",
    description="Generates ReAct reasoning loop (MAX_STEPS=5) via Groq LLM API and executes every tool call strictly through Agent WAF Proxy.",
)
async def run_agent_workflow(payload: AgentRunRequest) -> AgentRunResponse:
    """Submit a natural language goal for multi-step AI Agent workflow planning and policy-enforced execution."""
    logger.info(
        "Agent WAF Run API request received",
        extra={"goal": payload.goal, "session_id": payload.session_id},
    )

    try:
        waf_proxy = get_waf_proxy()
        workflow_engine = WorkflowExecutor(proxy=waf_proxy)
        result = await workflow_engine.run_agent_loop(goal=payload.goal, session_id=payload.session_id)
        return AgentRunResponse(**result)

    except Exception as exc:
        logger.exception("Failed to execute agent workflow through WAF proxy", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow execution failed: {str(exc)}",
        ) from exc

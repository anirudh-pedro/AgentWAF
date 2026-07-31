import json
import re
import time
import uuid
from typing import Any

from agent.executor import AgentToolExecutor
from agent.groq_planner import GroqPlanner
from logger import get_logger
from proxy.proxy import AgentWAFProxy
from rules.engine import RuleEngine, RuleEnginePolicyEvaluator
from tools.loader import register_builtin_tools
from tools.schemas import ToolRequest

logger = get_logger(__name__)

_proxy_instance: AgentWAFProxy | None = None
MAX_STEPS = 10


def get_waf_proxy() -> AgentWAFProxy:
    """Singleton getter for Agent WAF Proxy."""
    global _proxy_instance
    if _proxy_instance is None:
        register_builtin_tools()
        rule_engine = RuleEngine.get_instance()
        inner_executor = AgentToolExecutor()
        policy_evaluator = RuleEnginePolicyEvaluator(engine=rule_engine)
        _proxy_instance = AgentWAFProxy(inner_executor=inner_executor, evaluator=policy_evaluator)
    return _proxy_instance


class WorkflowValidationError(Exception):
    """Raised when a proposed tool choice violates domain workflow semantics before WAF evaluation."""
    pass


class WorkflowValidator:
    """Pure validation gate checking proposed tool choices against domain workflow semantics without mutating parameters."""

    @staticmethod
    def validate_step(tool_name: str, parameters: dict[str, Any], goal: str, history: list[dict[str, Any]]) -> bool:
        """Validate step semantics. Returns True if valid, raises WorkflowValidationError if invalid."""
        param_str = json.dumps(parameters).lower()
        goal_lower = goal.lower()

        # Rule 1: Invoice resource context must never use generic file tools
        is_invoice_context = "invoice" in goal_lower or "inv-" in goal_lower or "inv-" in param_str or "invoice" in param_str
        if is_invoice_context and tool_name.lower() in ("downloadfile", "download_file", "searchfiles", "search_files"):
            raise WorkflowValidationError(
                f"Proposed tool '{tool_name}' is invalid for invoice resource context. Use DownloadInvoice/SearchInvoice instead."
            )

        # Rule 2: Prevent duplicate SendEmail action steps in sequence
        if history and history[-1].get("tool", "").lower() == "sendemail" and tool_name.lower() == "sendemail":
            raise WorkflowValidationError(
                "Duplicate SendEmail step detected. Combine attachment into the original SendEmail call."
            )

        return True


class WorkflowExecutor:
    """Workflow Execution Engine running an iterative ReAct reasoning loop through Agent WAF inspection."""

    def __init__(self, proxy: AgentWAFProxy | None = None, planner: GroqPlanner | None = None) -> None:
        self.proxy = proxy or get_waf_proxy()
        self.planner = planner or GroqPlanner()
        self.validator = WorkflowValidator()

    async def run_agent_loop(self, goal: str, session_id: str | None = None) -> dict[str, Any]:
        """Run an iterative ReAct agent loop (MAX_STEPS = 5) routing every tool call through Agent WAF."""
        session_id = session_id or f"session-{uuid.uuid4().hex[:8]}"
        start_time = time.perf_counter()

        executed_steps: list[dict[str, Any]] = []
        history: list[dict[str, Any]] = []
        is_blocked = False
        blocked_step: dict[str, Any] | None = None
        final_response_str: str | None = None

        logger.info(
            "Starting ReAct Agent Loop",
            extra={"goal": goal, "max_steps": MAX_STEPS, "session_id": session_id},
        )

        for step_idx in range(1, MAX_STEPS + 1):
            # 1. Ask Groq Planner for next tool choice (Planner + Semantic Guard)
            step_plan = await self.planner.get_next_step(goal, history)
            tool_name = step_plan.get("tool", "FINISH")

            # Check if LLM decided to finish
            if tool_name.upper() == "FINISH":
                final_response_str = step_plan.get("final_response") or f"Goal '{goal}' achieved successfully."
                logger.info("Agent loop finished by planner choice", extra={"step_index": step_idx})
                break

            parameters = step_plan.get("parameters", {})

            # 2. Workflow Validator (Validation ONLY — checks & reports errors without modifying choices)
            try:
                self.validator.validate_step(tool_name, parameters, goal, history)
                logger.info(f"[Workflow Validator] Step #{step_idx} ('{tool_name}') passed workflow validation")
            except WorkflowValidationError as err:
                logger.warning(
                    f"[Workflow Validator] Step #{step_idx} validation failed: {str(err)}",
                    extra={"tool": tool_name, "parameters": parameters, "goal": goal},
                )

            req_id = f"req-{uuid.uuid4().hex[:8]}"

            tool_req = ToolRequest(
                tool_name=tool_name,
                parameters=parameters,
                request_id=req_id,
                session_id=session_id,
            )

            # 3. EVERY single tool call MUST pass through Agent WAF Proxy
            tool_resp = await self.proxy.execute_tool(tool_req)

            meta = tool_resp.metadata or {}
            policy_res = meta.get("policy_result") or ("ALLOW" if tool_resp.success else "BLOCK")
            risk_sc = float(meta.get("risk_score", 0.0))
            matched_rls = meta.get("matched_rules", [])
            violation_list = meta.get("violations", [])
            reason_str = meta.get("reason") or tool_resp.error

            step_record = {
                "step_index": step_idx,
                "tool": tool_name,
                "parameters": parameters,
                "status": policy_res,
                "risk": risk_sc,
                "matched_rules": matched_rls,
                "violations": violation_list,
                "reason": reason_str if policy_res == "BLOCK" else None,
                "thought": step_plan.get("thought"),
                "output": tool_resp.result if (policy_res in ("ALLOW", "SHADOW_BLOCK") and tool_resp.success) else None,
                "execution_time_ms": round(tool_resp.execution_time_ms, 2),
            }
            executed_steps.append(step_record)

            # 4. Append observation to history for next ReAct loop iteration
            history.append({
                "tool": tool_name,
                "parameters": parameters,
                "status": policy_res,
                "observation": tool_resp.result if tool_resp.success else tool_resp.error,
            })

            # 5. Active Enforcement Mode BLOCK decision -> HALT reasoning loop immediately!
            if policy_res == "BLOCK":
                is_blocked = True
                blocked_step = step_record
                logger.warning(
                    "ReAct Agent Loop HALTED by Agent WAF",
                    extra={"goal": goal, "step": step_idx, "tool": tool_name, "reason": reason_str},
                )
                break

        total_duration = round((time.perf_counter() - start_time) * 1000, 2)
        overall_status = "blocked" if is_blocked else "completed"

        if not final_response_str:
            if is_blocked and blocked_step:
                final_response_str = (
                    f"Agent execution was BLOCKED by Agent WAF at Step #{blocked_step['step_index']} "
                    f"({blocked_step['tool']}) due to security rule violation: {blocked_step['matched_rules']}."
                )
            else:
                final_response_str = f"Agent workflow completed ({len(executed_steps)} steps executed)."

        return {
            "workflow": f"Agent Workflow: {goal[:40]}...",
            "goal": goal,
            "status": overall_status,
            "session_id": session_id,
            "total_steps": len(executed_steps),
            "steps": executed_steps,
            "blocked_info": blocked_step if is_blocked else None,
            "final_response": final_response_str,
            "total_execution_time_ms": total_duration,
        }

    async def execute_workflow(
        self, plan: dict[str, Any], session_id: str | None = None
    ) -> dict[str, Any]:
        """Legacy helper running batch plan for backwards compatibility."""
        goal = plan.get("workflow") or "Batch Workflow"
        return await self.run_agent_loop(goal=goal, session_id=session_id)

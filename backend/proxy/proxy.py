from abc import ABC, abstractmethod
import time
from datetime import datetime, timezone
from typing import Any

from config import get_settings
from logger import get_logger
from tools.schemas import ToolRequest, ToolResponse
from .models import InspectionContext, PolicyDecision, PolicyEvaluationResult

logger = get_logger(__name__)


class BasePolicyEvaluator(ABC):
    """Abstract base class for security policy evaluators."""

    @abstractmethod
    async def evaluate(
        self, request: ToolRequest, context: InspectionContext
    ) -> PolicyEvaluationResult:
        """Evaluate a tool request against security policies and return a PolicyEvaluationResult."""
        pass


class DefaultPolicyEvaluator(BasePolicyEvaluator):
    """Default pass-through policy evaluator returning ALLOW for all requests."""

    async def evaluate(
        self, request: ToolRequest, context: InspectionContext
    ) -> PolicyEvaluationResult:
        start_time = time.perf_counter()
        duration_ms = (time.perf_counter() - start_time) * 1000
        return PolicyEvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason="Default pass-through policy allowed request execution",
            risk_score=0.0,
            rule_id=None,
            matched_rules=[],
            violations=[],
            recommendations=[],
            evaluation_time_ms=duration_ms,
        )


class AgentWAFProxy:
    """Policy-enforcing security proxy wrapping tool execution.
    
    Exposes the exact same interface signature (execute_tool) as AgentToolExecutor,
    enabling transparent dependency injection into LangGraph Agent runtime.
    """

    def __init__(
        self,
        inner_executor: Any,
        evaluator: BasePolicyEvaluator | None = None,
    ) -> None:
        if inner_executor is None:
            raise ValueError("inner_executor cannot be None")
        self.settings = get_settings()
        self.inner_executor = inner_executor
        self.evaluator = evaluator or DefaultPolicyEvaluator()

    @property
    def proxy_version(self) -> str:
        """Sourced directly from application version settings to avoid duplicated version strings."""
        return self.settings.APP_VERSION

    def discover_tools(self) -> list[dict[str, Any]]:
        """Delegate tool discovery to inner executor."""
        return self.inner_executor.discover_tools()

    async def execute_tool(self, request: ToolRequest) -> ToolResponse:
        """Inspect ToolRequest, evaluate policy, and conditionally forward or block execution."""
        inspection_start = time.perf_counter()
        dt_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        logger.info(
            "Agent WAF Proxy inspection started",
            extra={
                "tool_name": request.tool_name,
                "request_id": request.request_id,
                "agent_id": request.agent_id,
            },
        )

        # 1. Build Inspection Context
        context = InspectionContext(
            tool_name=request.tool_name,
            parameters=request.parameters,
            agent_id=request.agent_id,
            request_id=request.request_id,
            session_id=request.session_id,
            metadata=request.metadata,
            timestamp=dt_str,
        )

        # 2. Evaluate Policy (Fail Closed Safety)
        try:
            eval_result = await self.evaluator.evaluate(request, context)
        except Exception as exc:
            inspection_duration = (time.perf_counter() - inspection_start) * 1000
            logger.exception(
                "Agent WAF policy evaluation failed - Failing Closed",
                extra={
                    "tool_name": request.tool_name,
                    "request_id": request.request_id,
                    "error": str(exc),
                },
            )
            return ToolResponse(
                success=False,
                result=None,
                error="Agent WAF policy evaluation failed",
                execution_time_ms=inspection_duration,
                metadata={
                    "policy_result": "BLOCK",
                    "blocked": True,
                    "proxy_version": self.proxy_version,
                    "reason": "Policy evaluator exception (Fail Closed)",
                    "trace_id": request.metadata.get("trace_id", request.request_id),
                    "graph_run_id": request.metadata.get("graph_run_id"),
                },
            )

        inspection_duration = (time.perf_counter() - inspection_start) * 1000

        # Extract tracing metadata from request
        trace_id = request.metadata.get("trace_id") or request.request_id
        graph_run_id = request.metadata.get("graph_run_id")

        # 3. Handle BLOCK Decision
        if eval_result.decision == PolicyDecision.BLOCK:
            logger.warning(
                "Agent WAF Proxy BLOCKED tool execution",
                extra={
                    "tool_name": request.tool_name,
                    "request_id": request.request_id,
                    "reason": eval_result.reason,
                    "risk_score": eval_result.risk_score,
                    "rule_id": eval_result.rule_id,
                    "violations": eval_result.violations,
                },
            )
            return ToolResponse(
                success=False,
                result=None,
                error="Execution blocked by Agent WAF",
                execution_time_ms=inspection_duration,
                metadata={
                    "policy_result": "BLOCK",
                    "blocked": True,
                    "reason": eval_result.reason or "Security policy violation",
                    "risk_score": eval_result.risk_score,
                    "rule_id": eval_result.rule_id,
                    "matched_rules": eval_result.matched_rules,
                    "violations": eval_result.violations,
                    "recommendations": eval_result.recommendations,
                    "inspection_duration_ms": inspection_duration,
                    "proxy_version": self.proxy_version,
                    "trace_id": trace_id,
                    "graph_run_id": graph_run_id,
                },
            )

        # 4. Handle ALLOW Decision -> Forward to inner executor
        logger.info(
            "Agent WAF Proxy ALLOWED request - forwarding to inner executor",
            extra={
                "tool_name": request.tool_name,
                "request_id": request.request_id,
                "risk_score": eval_result.risk_score,
            },
        )

        response = await self.inner_executor.execute_tool(request)

        # 5. Non-Destructive Metadata Merge: preserve tool metadata for existing keys
        audit_metadata: dict[str, Any] = {
            "policy_result": "ALLOW",
            "blocked": False,
            "reason": eval_result.reason,
            "risk_score": eval_result.risk_score,
            "matched_rules": eval_result.matched_rules,
            "inspection_duration_ms": inspection_duration,
            "proxy_version": self.proxy_version,
            "trace_id": trace_id,
            "graph_run_id": graph_run_id,
        }

        merged_metadata = dict(response.metadata)
        for k, v in audit_metadata.items():
            if k not in merged_metadata or merged_metadata[k] is None:
                merged_metadata[k] = v

        return ToolResponse(
            success=response.success,
            result=response.result,
            error=response.error,
            execution_time_ms=response.execution_time_ms,
            metadata=merged_metadata,
        )

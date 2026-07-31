import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from config import get_settings
from logger import get_logger
from tools.base import BaseTool
from tools.schemas import ToolRequest, ToolResponse
from .models import BasePolicyEvaluator, InspectionContext, PolicyDecision, PolicyEvaluationResult
from .output_guard import ToolOutputGuard
from .sanitizer import redact_secrets

logger = get_logger(__name__)


class AgentWAFProxy(BaseTool):
    """Transparent Policy-Enforcing Proxy wrapping inner AgentToolExecutor.

    Intercepts all tool execution calls, evaluates security rules, records audit logs,
    and supports both Fail-Closed protection and Shadow Mode rule calibration.
    """

    def __init__(
        self,
        inner_executor: Any,
        evaluator: BasePolicyEvaluator,
        proxy_version: str = "1.0.0",
        output_guard: ToolOutputGuard | None = None,
    ) -> None:
        self.inner_executor = inner_executor
        self.evaluator = evaluator
        self.proxy_version = proxy_version
        self.output_guard = output_guard or ToolOutputGuard()

    @property
    def name(self) -> str:
        return "agent_waf_proxy"

    @property
    def description(self) -> str:
        return "Policy-enforcing transparent security proxy for AI Agent tool calls."

    @property
    def version(self) -> str:
        return self.proxy_version

    @property
    def category(self) -> str:
        return "security"

    def _publish_audit_event(
        self,
        request: ToolRequest,
        policy_result: str,
        risk_score: float,
        matched_rules: list[str],
        violations: list[str],
        execution_time_ms: float,
        dt_str: str,
        eval_result: PolicyEvaluationResult | None = None,
    ) -> None:
        """Helper to fire-and-forget extended audit log events to PostgreSQL (Neon)."""
        from dashboard.models import AuditEvent
        from dashboard.publisher import AuditEventPublisher

        settings = get_settings()

        # Extract sequence and scope metadata
        seq_metadata = (eval_result.metadata if eval_result and eval_result.metadata else {})
        previous_tool = seq_metadata.get("previous_tool")
        sequence_status = seq_metadata.get("sequence_status", "VALID" if policy_result == "ALLOW" else "VIOLATION" if "RULE-SEC-SEQUENCE-006" in matched_rules else None)
        requested_resource = seq_metadata.get("requested_resource") or request.parameters.get("customer_id") or request.parameters.get("resource_id") or request.parameters.get("file")
        agent_scope = request.metadata.get("agent_scope") or "default-scope"

        # Redact any secret credentials in parameters before audit log publishing
        sanitized_parameters = redact_secrets(request.parameters)

        event = AuditEvent(
            event_id=f"evt-{request.request_id}",
            request_id=request.request_id,
            timestamp=dt_str,
            tool_name=request.tool_name,
            action="EXECUTE",
            policy_result=policy_result,
            risk_score=risk_score,
            matched_rules=matched_rules,
            violations=violations,
            parameters=sanitized_parameters,
            agent_scope=str(agent_scope) if agent_scope else None,
            requested_resource=str(requested_resource) if requested_resource else None,
            previous_tool=str(previous_tool) if previous_tool else None,
            current_tool=request.tool_name,
            sequence_status=sequence_status,
            waf_mode=settings.WAF_MODE,
            execution_time_ms=execution_time_ms,
        )
        AuditEventPublisher.get_instance().publish(event)

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Delegate to execute_tool for BaseTool protocol compatibility."""
        return await self.execute_tool(request)

    async def execute_tool(self, request: ToolRequest) -> ToolResponse:
        """Main security inspection flow for intercepting agent tool requests."""
        settings = get_settings()
        inspection_start = time.perf_counter()
        now_dt = datetime.now(timezone.utc)
        dt_str = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        logger.info(
            "Agent WAF Proxy inspection started",
            extra={
                "request_id": request.request_id,
                "tool_name": request.tool_name,
                "agent_id": request.agent_id,
                "waf_mode": settings.WAF_MODE,
            },
        )

        context = InspectionContext(
            agent_id=request.agent_id or "default-agent",
            session_id=request.session_id or "default-session",
            timestamp=now_dt,
            request_id=request.request_id,
            metadata=request.metadata,
        )

        # 1. Evaluate Security Policy Rules
        try:
            eval_result: PolicyEvaluationResult = await self.evaluator.evaluate(request, context)
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
            self._publish_audit_event(
                request, "BLOCK", 1.0, ["FAIL_CLOSED_EXCEPTION"], [str(exc)], inspection_duration, dt_str
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

        # 2. Handle BLOCK Decision (with WAF_MODE=SHADOW support)
        if eval_result.decision == PolicyDecision.BLOCK:
            if settings.is_shadow_mode:
                logger.warning(
                    "Agent WAF Proxy SHADOW MODE: would have BLOCKED tool execution",
                    extra={
                        "tool_name": request.tool_name,
                        "request_id": request.request_id,
                        "reason": eval_result.reason,
                        "risk_score": eval_result.risk_score,
                        "rule_id": eval_result.rule_id,
                        "violations": eval_result.violations,
                        "waf_mode": "SHADOW",
                    },
                )
                self._publish_audit_event(
                    request,
                    "SHADOW_BLOCK",
                    eval_result.risk_score,
                    eval_result.matched_rules,
                    eval_result.violations,
                    inspection_duration,
                    dt_str,
                    eval_result,
                )
                # In shadow mode, log violation as SHADOW_BLOCK but execute tool safely
                raw_response = await self.inner_executor.execute_tool(request)
                response = self.output_guard.inspect_and_sanitize_response(raw_response)
                response.metadata.update(
                    {
                        "shadow_mode": True,
                        "would_have_blocked": True,
                        "policy_result": "SHADOW_BLOCK",
                        "risk_score": eval_result.risk_score,
                        "matched_rules": eval_result.matched_rules,
                        "violations": eval_result.violations,
                        "waf_mode": "SHADOW",
                    }
                )
                return response

            # Active Enforcement Mode: Block tool call
            logger.warning(
                "Agent WAF Proxy BLOCKED tool execution",
                extra={
                    "tool_name": request.tool_name,
                    "request_id": request.request_id,
                    "reason": eval_result.reason,
                    "risk_score": eval_result.risk_score,
                    "rule_id": eval_result.rule_id,
                    "violations": eval_result.violations,
                    "waf_mode": "ENFORCE",
                },
            )
            self._publish_audit_event(
                request,
                "BLOCK",
                eval_result.risk_score,
                eval_result.matched_rules,
                eval_result.violations,
                inspection_duration,
                dt_str,
                eval_result,
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
                    "waf_mode": "ENFORCE",
                    "trace_id": trace_id,
                    "graph_run_id": graph_run_id,
                },
            )

        # 3. Handle ALLOW Decision -> Forward to inner executor & apply ToolOutputGuard
        logger.info(
            "Agent WAF Proxy ALLOWED request - forwarding to inner executor",
            extra={
                "tool_name": request.tool_name,
                "request_id": request.request_id,
                "risk_score": eval_result.risk_score,
                "waf_mode": settings.WAF_MODE,
            },
        )

        raw_response = await self.inner_executor.execute_tool(request)
        response = self.output_guard.inspect_and_sanitize_response(raw_response)
        total_duration = inspection_duration + response.execution_time_ms

        self._publish_audit_event(
            request,
            "ALLOW",
            eval_result.risk_score,
            eval_result.matched_rules,
            [],
            total_duration,
            dt_str,
            eval_result,
        )

        # Merge metadata
        response.metadata.update(
            {
                "policy_result": "ALLOW",
                "blocked": False,
                "risk_score": eval_result.risk_score,
                "matched_rules": eval_result.matched_rules,
                "inspection_duration_ms": inspection_duration,
                "proxy_version": self.proxy_version,
                "waf_mode": settings.WAF_MODE,
                "trace_id": trace_id,
                "graph_run_id": graph_run_id,
            }
        )

        return response

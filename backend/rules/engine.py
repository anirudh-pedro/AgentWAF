import asyncio
import time
from threading import Lock
from typing import Any

from config import get_settings
from logger import get_logger
from proxy import BasePolicyEvaluator, InspectionContext, PolicyDecision, PolicyEvaluationResult
from tools.schemas import ToolRequest
from .base import BaseRule
from .builtin import DangerousToolRule, ParameterSizeRule, PromptInjectionRule, SQLInjectionRule
from .models import RuleResult

logger = get_logger(__name__)

_lock = Lock()


class RuleEngine:
    """Thread-safe Rule Engine supporting prioritized execution, metrics tracking, and dynamic rule reloads."""

    _instance: "RuleEngine | None" = None

    def __init__(self) -> None:
        self._rules: dict[str, BaseRule] = {}
        self._metrics: dict[str, dict[str, Any]] = {}
        self._register_default_rules()

    @classmethod
    def get_instance(cls) -> "RuleEngine":
        """Thread-safe singleton accessor for RuleEngine."""
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _register_default_rules(self) -> None:
        """Register built-in security rules on engine initialization."""
        default_rules = [
            PromptInjectionRule(),
            SQLInjectionRule(),
            DangerousToolRule(),
            ParameterSizeRule(),
        ]
        for rule in default_rules:
            self._register_internal(rule)

    def _register_internal(self, rule: BaseRule) -> None:
        """Internal helper to register rule and initialize metrics counters."""
        self._rules[rule.rule_id] = rule
        if rule.rule_id not in self._metrics:
            self._metrics[rule.rule_id] = {
                "total_executions": 0,
                "total_matches": 0,
                "total_evaluation_time_ms": 0.0,
            }

    def register_rule(self, rule: BaseRule) -> None:
        """Register a new security rule dynamically into the engine."""
        if not isinstance(rule, BaseRule):
            raise ValueError(f"Rule {rule} is not an instance of BaseRule")

        with _lock:
            self._register_internal(rule)
            logger.info("Registered security rule", extra={"rule_id": rule.rule_id, "name": rule.name, "priority": rule.priority})

    def unregister_rule(self, rule_id: str) -> None:
        """Unregister a security rule by rule_id."""
        with _lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                self._metrics.pop(rule_id, None)
                logger.info("Unregistered security rule", extra={"rule_id": rule_id})

    def reload_rules(self) -> None:
        """Dynamically re-read settings and refresh built-in rule instances."""
        get_settings.cache_clear()
        with _lock:
            self._rules.clear()
            self._register_default_rules()
            logger.info("Reloaded rule engine settings and built-in rules")

    def list_rules(self) -> list[dict[str, Any]]:
        """Return metadata and execution metrics for all registered security rules."""
        with _lock:
            sorted_rules = sorted(self._rules.values(), key=lambda r: r.priority)
            result: list[dict[str, Any]] = []

            for rule in sorted_rules:
                m = self._metrics.get(rule.rule_id, {"total_executions": 0, "total_matches": 0, "total_evaluation_time_ms": 0.0})
                execs = m["total_executions"]
                avg_time = (m["total_evaluation_time_ms"] / execs) if execs > 0 else 0.0

                result.append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "severity": rule.severity.value,
                    "priority": rule.priority,
                    "stop_on_match": rule.stop_on_match,
                    "tags": rule.tags,
                    "enabled": rule.enabled,
                    "metrics": {
                        "total_executions": execs,
                        "total_matches": m["total_matches"],
                        "avg_evaluation_time_ms": round(avg_time, 3),
                    },
                })
            return result

    async def evaluate_all(
        self, request: ToolRequest, context: InspectionContext
    ) -> PolicyEvaluationResult:
        """Evaluate all enabled security rules concurrently ordered by priority.
        
        Accumulates risk scores and tracks per-rule execution metrics.
        """
        start_time = time.perf_counter()
        settings = get_settings()

        with _lock:
            # Sort active rules by priority (lower value = higher priority)
            active_rules = sorted(
                [rule for rule in self._rules.values() if rule.enabled],
                key=lambda r: r.priority
            )

        if not active_rules:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return PolicyEvaluationResult(
                decision=PolicyDecision.ALLOW,
                reason="No active security rules enabled",
                risk_score=0.0,
                evaluation_time_ms=duration_ms,
            )

        # Run active rules concurrently
        tasks = [rule.evaluate(request, context) for rule in active_rules]
        t_start_rules = time.perf_counter()
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        rule_eval_duration = (time.perf_counter() - t_start_rules) * 1000

        matched_results: list[RuleResult] = []
        with _lock:
            for i, res in enumerate(raw_results):
                rule = active_rules[i]
                m = self._metrics.setdefault(rule.rule_id, {"total_executions": 0, "total_matches": 0, "total_evaluation_time_ms": 0.0})
                m["total_executions"] += 1
                m["total_evaluation_time_ms"] += rule_eval_duration

                if isinstance(res, Exception):
                    logger.exception(
                        "Rule evaluation failed with exception - ignoring individual rule failure",
                        extra={"rule_id": rule.rule_id, "error": str(res)}
                    )
                elif isinstance(res, RuleResult) and res.matched:
                    m["total_matches"] += 1
                    matched_results.append(res)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Calculate cumulative risk score (capped at 1.0)
        cumulative_risk = min(1.0, sum(r.risk_score for r in matched_results))

        matched_rule_ids = [r.rule_id for r in matched_results]
        violations = [r.violation for r in matched_results if r.violation]
        recommendations = [r.recommendation for r in matched_results if r.recommendation]
        primary_rule_id = matched_rule_ids[0] if matched_rule_ids else None

        threshold = settings.DEFAULT_RISK_THRESHOLD

        if cumulative_risk >= threshold:
            decision = PolicyDecision.BLOCK
            reason = f"Cumulative risk score ({cumulative_risk:.2f}) exceeded threshold ({threshold:.2f}). Rules matched: {matched_rule_ids}"
            logger.warning(
                "RuleEngine evaluated BLOCK decision",
                extra={
                    "request_id": request.request_id,
                    "cumulative_risk": cumulative_risk,
                    "threshold": threshold,
                    "matched_rules": matched_rule_ids,
                }
            )
        else:
            decision = PolicyDecision.ALLOW
            reason = f"Cumulative risk score ({cumulative_risk:.2f}) within acceptable threshold ({threshold:.2f})"
            logger.info(
                "RuleEngine evaluated ALLOW decision",
                extra={
                    "request_id": request.request_id,
                    "cumulative_risk": cumulative_risk,
                    "threshold": threshold,
                }
            )

        return PolicyEvaluationResult(
            decision=decision,
            reason=reason,
            risk_score=cumulative_risk,
            rule_id=primary_rule_id,
            matched_rules=matched_rule_ids,
            violations=violations,
            recommendations=recommendations,
            evaluation_time_ms=duration_ms,
        )


class RuleEnginePolicyEvaluator(BasePolicyEvaluator):
    """Policy evaluator implementing Module 10 BasePolicyEvaluator via RuleEngine."""

    def __init__(self, engine: RuleEngine | None = None) -> None:
        self.engine = engine or RuleEngine.get_instance()

    async def evaluate(
        self, request: ToolRequest, context: InspectionContext
    ) -> PolicyEvaluationResult:
        """Bridge AgentWAFProxy inspection requests to RuleEngine evaluation."""
        return await self.engine.evaluate_all(request, context)

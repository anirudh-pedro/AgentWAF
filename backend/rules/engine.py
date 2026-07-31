import asyncio
import time
from threading import Lock
from typing import Any

from config import get_settings
from logger import get_logger
from proxy import BasePolicyEvaluator, InspectionContext, PolicyDecision, PolicyEvaluationResult
from tools.schemas import ToolRequest
from .base import BaseRule
from .builtin import (
    CredentialSecurityRule,
    DangerousToolRule,
    DataScopeRule,
    EmailSecurityRule,
    ParameterSizeRule,
    PromptInjectionRule,
    SQLInjectionRule,
    SequenceRule,
    ToolRateLimitRule,
)
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
            ToolRateLimitRule(),
            DataScopeRule(),
            SequenceRule(),
            EmailSecurityRule(),
            CredentialSecurityRule(),
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
        with _lock:
            self._register_internal(rule)
        logger.info(
            "Security rule registered dynamically",
            extra={"rule_id": rule.rule_id, "name": rule.name, "priority": rule.priority},
        )

    def list_rules(self) -> list[dict[str, Any]]:
        """Return structured summary metadata of all registered security rules."""
        with _lock:
            rules_summary = []
            for r in sorted(self._rules.values(), key=lambda rule: rule.priority):
                rules_summary.append(
                    {
                        "rule_id": r.rule_id,
                        "name": r.name,
                        "description": r.description,
                        "severity": r.severity.value,
                        "priority": r.priority,
                        "enabled": r.enabled,
                        "stop_on_match": r.stop_on_match,
                        "tags": r.tags,
                    }
                )
            return rules_summary

    async def evaluate_all(self, request: ToolRequest, context: InspectionContext) -> list[RuleResult]:
        """Evaluate all enabled security rules against tool request in priority order."""
        with _lock:
            active_rules = sorted(
                [r for r in self._rules.values() if r.enabled],
                key=lambda rule: rule.priority,
            )

        results: list[RuleResult] = []
        for rule in active_rules:
            start_time = time.perf_counter()
            try:
                res = await rule.evaluate(request, context)
                eval_time = (time.perf_counter() - start_time) * 1000

                with _lock:
                    m = self._metrics[rule.rule_id]
                    m["total_executions"] += 1
                    m["total_evaluation_time_ms"] += eval_time
                    if res.matched:
                        m["total_matches"] += 1

                results.append(res)

                if res.matched and rule.stop_on_match:
                    logger.debug(
                        "Stop on match rule triggered - skipping lower priority rules",
                        extra={"rule_id": rule.rule_id, "priority": rule.priority},
                    )
                    break

            except Exception as exc:
                eval_time = (time.perf_counter() - start_time) * 1000
                logger.exception(
                    "Rule evaluation encountered unhandled exception",
                    extra={"rule_id": rule.rule_id, "error": str(exc)},
                )
                results.append(
                    RuleResult(
                        matched=True,
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        risk_score=1.0,
                        violation=f"Rule evaluation exception: {str(exc)}",
                        recommendation="Fail closed on rule error",
                        reason="Rule evaluation threw unhandled exception",
                    )
                )
                if rule.stop_on_match:
                    break

        return results

    def get_metrics(self) -> list[dict[str, Any]]:
        """Return execution metrics per registered rule."""
        with _lock:
            metrics_summary = []
            for rule_id, m in self._metrics.items():
                rule = self._rules.get(rule_id)
                exec_count = m["total_executions"]
                avg_time = (m["total_evaluation_time_ms"] / exec_count) if exec_count > 0 else 0.0
                metrics_summary.append(
                    {
                        "rule_id": rule_id,
                        "rule_name": rule.name if rule else "Unknown",
                        "total_executions": exec_count,
                        "total_matches": m["total_matches"],
                        "average_evaluation_time_ms": round(avg_time, 3),
                    }
                )
            return metrics_summary


class RuleEnginePolicyEvaluator(BasePolicyEvaluator):
    """Bridge adapter connecting RuleEngine outputs to PolicyEvaluationResult for WAF proxy."""

    def __init__(self, engine: RuleEngine | None = None) -> None:
        self.engine = engine or RuleEngine.get_instance()

    async def evaluate(self, request: ToolRequest, context: InspectionContext) -> PolicyEvaluationResult:
        settings = get_settings()
        results = await self.engine.evaluate_all(request, context)

        # Merge metadata from all rule evaluations
        merged_meta: dict[str, Any] = {}
        for r in results:
            if r.metadata:
                merged_meta.update(r.metadata)

        matched_results = [r for r in results if r.matched]
        if not matched_results:
            logger.info("RuleEngine evaluated ALLOW decision", extra={"request_id": request.request_id})
            return PolicyEvaluationResult(
                decision=PolicyDecision.ALLOW,
                risk_score=0.0,
                reason="No policy violations detected",
                rule_id=None,
                matched_rules=[],
                violations=[],
                recommendations=[],
                metadata=merged_meta,
            )

        matched_rule_ids = [r.rule_id for r in matched_results]
        violations = [r.violation for r in matched_results if r.violation]
        recommendations = [r.recommendation for r in matched_results if r.recommendation]

        # Calculate cumulative risk score capped at 1.0
        cumulative_risk = min(1.0, sum(r.risk_score for r in matched_results))

        primary_rule = matched_results[0]
        decision = (
            PolicyDecision.BLOCK
            if cumulative_risk >= settings.RISK_THRESHOLD
            else PolicyDecision.ALLOW
        )

        logger.warning(
            f"RuleEngine evaluated {decision.value} decision",
            extra={
                "request_id": request.request_id,
                "cumulative_risk": cumulative_risk,
                "threshold": settings.RISK_THRESHOLD,
                "matched_rules": matched_rule_ids,
            },
        )

        return PolicyEvaluationResult(
            decision=decision,
            risk_score=round(cumulative_risk, 2),
            reason=primary_rule.reason or f"Cumulative risk score ({cumulative_risk:.2f}) exceeded threshold ({settings.RISK_THRESHOLD:.2f}). Rules matched: {matched_rule_ids}",
            rule_id=primary_rule.rule_id,
            matched_rules=matched_rule_ids,
            violations=violations,
            recommendations=recommendations,
            metadata=merged_meta,
        )

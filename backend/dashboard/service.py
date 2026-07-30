import os
import time
from collections import Counter
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable

from config import get_settings
from db import DatabaseManager
from logger import get_logger
from rules import RuleEngine
from tools import ToolRegistry
from .models import (
    AuditEvent,
    DashboardSummary,
    RiskStatistics,
    RuleStatistics,
    SystemHealth,
    TimeSeriesPoint,
    ToolStatistics,
)
from .publisher import AuditEventPublisher

logger = get_logger(__name__)

_lock = Lock()
_START_TIME = time.time()
_START_TIME_ISO = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class AuditEventPublisher:
    """Decoupled Event Publisher managing subscriber listeners for audit events."""

    _instance: "AuditEventPublisher | None" = None

    def __init__(self) -> None:
        self._subscribers: list[Callable[[AuditEvent], None]] = []

    @classmethod
    def get_instance(cls) -> "AuditEventPublisher":
        """Thread-safe singleton accessor for AuditEventPublisher."""
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def subscribe(self, callback: Callable[[AuditEvent], None]) -> None:
        """Register a subscriber callback listener for audit events."""
        with _lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def publish(self, event: AuditEvent) -> None:
        """Publish an audit event to all registered subscriber listeners."""
        with _lock:
            subscribers = list(self._subscribers)

        for callback in subscribers:
            try:
                callback(event)
            except Exception as exc:
                logger.warning("Error in audit event subscriber callback", extra={"error": str(exc)})


class DashboardService:
    """Read-only operational analytics and audit service for Agent WAF monitoring."""

    _instance: "DashboardService | None" = None
    MAX_AUDIT_LOG_SIZE: int = 1000

    def __init__(self) -> None:
        self._audit_events: list[AuditEvent] = []
        # Subscribe to AuditEventPublisher
        AuditEventPublisher.get_instance().subscribe(self.record_event)

    @classmethod
    def get_instance(cls) -> "DashboardService":
        """Thread-safe singleton accessor for DashboardService."""
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def record_event(self, event: AuditEvent) -> None:
        """Record an audit event into the in-memory event stream buffer."""
        with _lock:
            self._audit_events.append(event)
            if len(self._audit_events) > self.MAX_AUDIT_LOG_SIZE:
                self._audit_events.pop(0)

    def _calculate_time_series_trend(self, events: list[AuditEvent]) -> list[TimeSeriesPoint]:
        """Aggregate audit events into minute-based time-series buckets."""
        buckets: dict[str, list[AuditEvent]] = {}
        for e in events:
            bucket_key = e.timestamp[:16]  # "YYYY-MM-DDTHH:MM"
            buckets.setdefault(bucket_key, []).append(e)

        trend: list[TimeSeriesPoint] = []
        for bucket_key in sorted(buckets.keys())[-10:]:
            b_events = buckets[bucket_key]
            tot = len(b_events)
            blk = sum(1 for ev in b_events if ev.policy_result == "BLOCK")
            avg_r = sum(ev.risk_score for ev in b_events) / tot if tot > 0 else 0.0
            trend.append(
                TimeSeriesPoint(
                    timestamp_bucket=bucket_key,
                    total_requests=tot,
                    blocked_requests=blk,
                    average_risk=round(avg_r, 3),
                )
            )
        return trend

    def get_summary(self) -> DashboardSummary:
        """Aggregate operational summary metrics from audit history and registered engines."""
        settings = get_settings()

        with _lock:
            events = list(self._audit_events)

        total_requests = len(events)
        allowed_requests = sum(1 for e in events if e.policy_result == "ALLOW")
        blocked_requests = sum(1 for e in events if e.policy_result == "BLOCK")

        avg_risk = (sum(e.risk_score for e in events) / total_requests) if total_requests > 0 else 0.0
        avg_exec_time = (sum(e.execution_time_ms for e in events) / total_requests) if total_requests > 0 else 0.0

        rule_counter: Counter[str] = Counter()
        for e in events:
            for rule_id in e.matched_rules:
                rule_counter[rule_id] += 1
        top_rule = rule_counter.most_common(1)[0][0] if rule_counter else None

        tool_counter: Counter[str] = Counter(e.tool_name for e in events)
        top_tool = tool_counter.most_common(1)[0][0] if tool_counter else None

        trend = self._calculate_time_series_trend(events)

        return DashboardSummary(
            total_requests=total_requests,
            allowed_requests=allowed_requests,
            blocked_requests=blocked_requests,
            average_risk_score=round(avg_risk, 3),
            average_execution_time_ms=round(avg_exec_time, 2),
            top_triggered_rule=top_rule,
            top_used_tool=top_tool,
            proxy_version=settings.APP_VERSION,
            recent_trend=trend,
        )

    def get_audit_events(
        self,
        tool: str | None = None,
        decision: str | None = None,
        rule: str | None = None,
        limit: int = 50,
    ) -> list[AuditEvent]:
        """Query recent audit events with optional field filtering."""
        with _lock:
            events = list(reversed(self._audit_events))

        filtered: list[AuditEvent] = []
        for e in events:
            if tool and e.tool_name.lower() != tool.lower():
                continue
            if decision and e.policy_result.upper() != decision.upper():
                continue
            if rule and rule not in e.matched_rules:
                continue
            filtered.append(e)
            if len(filtered) >= limit:
                break

        return filtered

    def get_rule_stats(self) -> list[RuleStatistics]:
        """Retrieve aggregated rule statistics directly from RuleEngine metrics."""
        engine_rules = RuleEngine.get_instance().list_rules()

        with _lock:
            events = list(self._audit_events)

        last_triggered_map: dict[str, str] = {}
        for e in reversed(events):
            for r_id in e.matched_rules:
                if r_id not in last_triggered_map:
                    last_triggered_map[r_id] = e.timestamp

        results: list[RuleStatistics] = []
        for r_meta in engine_rules:
            r_id = r_meta["rule_id"]
            m = r_meta.get("metrics", {})
            results.append(
                RuleStatistics(
                    rule_id=r_id,
                    rule_name=r_meta["name"],
                    total_matches=m.get("total_matches", 0),
                    average_risk=0.8 if m.get("total_matches", 0) > 0 else 0.0,
                    average_execution_time_ms=m.get("avg_evaluation_time_ms", 0.0),
                    last_triggered=last_triggered_map.get(r_id),
                    enabled=r_meta.get("enabled", True),
                )
            )

        return results

    def get_tool_stats(self) -> list[ToolStatistics]:
        """Retrieve aggregated tool invocation statistics."""
        registered_tools = [t["name"] for t in ToolRegistry.get_instance().list_tools()]

        with _lock:
            events = list(self._audit_events)

        tool_metrics: dict[str, dict[str, Any]] = {
            t_name: {"total": 0, "allowed": 0, "blocked": 0, "total_latency": 0.0}
            for t_name in registered_tools
        }

        for e in events:
            if e.tool_name not in tool_metrics:
                tool_metrics[e.tool_name] = {"total": 0, "allowed": 0, "blocked": 0, "total_latency": 0.0}
            tm = tool_metrics[e.tool_name]
            tm["total"] += 1
            if e.policy_result == "ALLOW":
                tm["allowed"] += 1
            else:
                tm["blocked"] += 1
            tm["total_latency"] += e.execution_time_ms

        results: list[ToolStatistics] = []
        for tool_name, metrics in tool_metrics.items():
            total = metrics["total"]
            avg_lat = (metrics["total_latency"] / total) if total > 0 else 0.0
            results.append(
                ToolStatistics(
                    tool_name=tool_name,
                    total_calls=total,
                    allowed_calls=metrics["allowed"],
                    blocked_calls=metrics["blocked"],
                    average_latency_ms=round(avg_lat, 2),
                )
            )

        return results

    def get_risk_stats(self) -> RiskStatistics:
        """Calculate threat distribution and time-series risk metrics across audited requests."""
        with _lock:
            events = list(self._audit_events)

        if not events:
            return RiskStatistics(
                average_risk_score=0.0,
                highest_observed_risk=0.0,
                blocked_percentage=0.0,
                risk_distribution={"low": 0, "medium": 0, "high": 0, "critical": 0},
                time_series_trend=[],
            )

        total = len(events)
        avg_risk = sum(e.risk_score for e in events) / total
        max_risk = max(e.risk_score for e in events)
        blocked_count = sum(1 for e in events if e.policy_result == "BLOCK")
        blocked_pct = (blocked_count / total) * 100.0

        dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for e in events:
            r = e.risk_score
            if r < 0.3:
                dist["low"] += 1
            elif r < 0.6:
                dist["medium"] += 1
            elif r < 0.85:
                dist["high"] += 1
            else:
                dist["critical"] += 1

        trend = self._calculate_time_series_trend(events)

        return RiskStatistics(
            average_risk_score=round(avg_risk, 3),
            highest_observed_risk=round(max_risk, 3),
            blocked_percentage=round(blocked_pct, 1),
            risk_distribution=dist,
            time_series_trend=trend,
        )

    async def get_system_health(self) -> SystemHealth:
        """Check system readiness, database health, process uptime, memory usage, and versioning."""
        settings = get_settings()
        db_mgr = DatabaseManager.get_instance()
        db_healthy = await db_mgr.check_health()

        rules = RuleEngine.get_instance().list_rules()
        total_rules = len(rules)
        enabled_rules = sum(1 for r in rules if r.get("enabled", True))
        registered_tools = [t["name"] for t in ToolRegistry.get_instance().list_tools()]

        uptime = time.time() - _START_TIME

        # Process memory estimate
        mem_mb = 0.0
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / (1024 * 1024)
        except Exception:
            pass

        active_modules = [
            "Module 1 – Project Bootstrap",
            "Module 2 – Configuration",
            "Module 3 – Logging",
            "Module 4 – Database Foundation",
            "Module 5 – Pure ASGI Middleware",
            "Module 6 – API Layer",
            "Module 7 – Tool Framework",
            "Module 8 – Sample Tools",
            "Module 9 – LangGraph Runtime",
            "Module 10 – Agent WAF Proxy",
            "Module 11 – Rule Engine",
            "Module 12 – Dashboard & Audit Analytics",
        ]

        return SystemHealth(
            proxy_version=settings.APP_VERSION,
            rule_count=total_rules,
            enabled_rule_count=enabled_rules,
            registered_tools=registered_tools,
            database_status="healthy" if db_healthy else "unhealthy",
            uptime_seconds=round(uptime, 2),
            start_time=_START_TIME_ISO,
            memory_usage_mb=round(mem_mb, 2),
            active_modules=active_modules,
        )

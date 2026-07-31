from typing import Any
from fastapi import APIRouter, Response, status

from agent.groq_planner import GroqPlanner
from config import get_settings
from dashboard.service import DashboardService
from db import DatabaseManager
from rules import RuleEngine
from rules.builtin import SequenceRule

router = APIRouter(tags=["Health & Observability Status"])


@router.get(
    "/",
    summary="Root Service Status",
    description="Returns root application metadata and running status.",
)
async def root_info() -> dict[str, Any]:
    settings = get_settings()
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "waf_mode": settings.WAF_MODE,
    }


@router.get(
    "/health",
    summary="General Health Check",
    description="Simple health check for server availability.",
)
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get(
    "/ready",
    summary="Readiness Probe",
    description="Checks downstream database connectivity to confirm application readiness.",
)
async def readiness_check(response: Response) -> dict[str, Any]:
    db_manager = DatabaseManager.get_instance()
    is_healthy = await db_manager.check_health()

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"database": "unhealthy", "ready": False}

    return {"database": "healthy", "ready": True}


@router.get(
    "/live",
    summary="Liveness Probe",
    description="Kubernetes/AWS ECS liveness probe.",
)
async def liveness_check() -> dict[str, bool]:
    return {"alive": True}


@router.get(
    "/metrics",
    summary="Prometheus & Observability Metrics",
    description="Exposes structured telemetry counters and latency histograms for AWS CloudWatch and Prometheus scraping.",
)
async def get_observability_metrics() -> dict[str, Any]:
    """Return observability metrics including total request counters, threat blocks, and latency stats."""
    settings = get_settings()
    db_manager = DatabaseManager.get_instance()
    db_healthy = await db_manager.check_health()

    service = DashboardService.get_instance()
    summary = await service.get_summary()
    audit_events = await service.get_audit_events(limit=500)

    # Compute metric counters
    shadow_events = sum(1 for e in audit_events if e.policy_result == "SHADOW_BLOCK")
    scope_blocks = sum(1 for e in audit_events if "RULE-SEC-DATA-SCOPE-005" in (e.matched_rules or []))
    sequence_blocks = sum(1 for e in audit_events if "RULE-SEC-SEQUENCE-006" in (e.matched_rules or []))
    active_sessions_count = len(SequenceRule._session_history)

    planner_metrics = GroqPlanner.get_planner_metrics()

    return {
        "agent_waf_requests_total": summary.total_requests,
        "agent_waf_requests_allowed_total": summary.allowed_requests,
        "agent_waf_requests_blocked_total": summary.blocked_requests,
        "agent_waf_risk_score_average": summary.average_risk_score,
        "agent_waf_latency_ms_average": summary.average_execution_time_ms,
        "agent_waf_database_status": 1 if db_healthy else 0,
        "agent_waf_top_triggered_rule": summary.top_triggered_rule,
        "agent_waf_top_used_tool": summary.top_used_tool,
        # Mandatory Challenge Metrics
        "shadow_events_total": shadow_events,
        "sequence_rule_blocks": sequence_blocks,
        "scope_rule_blocks": scope_blocks,
        "active_sessions": active_sessions_count,
        "current_waf_mode": settings.WAF_MODE,
        # Groq Planner Observability Metrics
        "planner_metrics": planner_metrics,
    }

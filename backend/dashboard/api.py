from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from logger import get_logger
from .models import (
    AuditEvent,
    DashboardSummary,
    RiskStatistics,
    RuleStatistics,
    SystemHealth,
    ToolStatistics,
)
from .service import DashboardService
from .websocket import ws_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Audit Analytics"])


@router.websocket("/ws")
async def websocket_dashboard_endpoint_alt(websocket: WebSocket) -> None:
    """Alternative WebSocket endpoint /dashboard/ws."""
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Retrieve Dashboard Summary Metrics",
    description="Returns aggregated operational statistics for Agent WAF activity from PostgreSQL.",
)
async def get_dashboard_summary() -> DashboardSummary:
    """Retrieve top-level operational summary metrics from PostgreSQL (Neon)."""
    logger.info("Dashboard API request: /dashboard/summary")
    try:
        service = DashboardService.get_instance()
        return await service.get_summary()
    except Exception as exc:
        logger.exception("Failed to retrieve dashboard summary metrics", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to aggregate dashboard summary metrics",
        ) from exc


@router.get(
    "/audit",
    response_model=list[AuditEvent],
    summary="Retrieve Audit Log Timeline",
    description="Returns recent audit events from PostgreSQL with optional tool, decision, and rule filters.",
)
async def get_audit_timeline(
    tool: Annotated[str | None, Query(description="Filter by tool name")] = None,
    decision: Annotated[str | None, Query(description="Filter by decision (ALLOW or BLOCK)")] = None,
    rule: Annotated[str | None, Query(description="Filter by matched rule ID")] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Maximum items to return")] = 50,
) -> list[AuditEvent]:
    """Retrieve audit timeline from PostgreSQL (Neon) with optional filtering."""
    logger.info(
        "Dashboard API request: /dashboard/audit",
        extra={"filter_tool": tool, "filter_decision": decision, "filter_rule": rule, "limit": limit},
    )

    if decision and decision.upper() not in ("ALLOW", "BLOCK", "SHADOW_BLOCK"):
        logger.warning("Invalid decision filter passed to audit API", extra={"decision": decision})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filter 'decision' must be either 'ALLOW', 'BLOCK', or 'SHADOW_BLOCK'",
        )

    try:
        service = DashboardService.get_instance()
        return await service.get_audit_events(tool=tool, decision=decision, rule=rule, limit=limit)
    except Exception as exc:
        logger.exception("Failed to retrieve audit timeline", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit timeline",
        ) from exc


@router.get(
    "/rules",
    response_model=list[RuleStatistics],
    summary="Retrieve Security Rule Analytics",
    description="Returns operational performance metrics for registered security rules from PostgreSQL.",
)
async def get_rule_analytics() -> list[RuleStatistics]:
    """Retrieve rule execution statistics and hit counts from PostgreSQL (Neon)."""
    logger.info("Dashboard API request: /dashboard/rules")
    try:
        service = DashboardService.get_instance()
        return await service.get_rule_stats()
    except Exception as exc:
        logger.exception("Failed to retrieve rule analytics", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rule analytics",
        ) from exc


@router.get(
    "/tools",
    response_model=list[ToolStatistics],
    summary="Retrieve Tool Usage Analytics",
    description="Returns invocation latency and call volume metrics per registered tool from PostgreSQL.",
)
async def get_tool_analytics() -> list[ToolStatistics]:
    """Retrieve tool invocation statistics from PostgreSQL (Neon)."""
    logger.info("Dashboard API request: /dashboard/tools")
    try:
        service = DashboardService.get_instance()
        return await service.get_tool_stats()
    except Exception as exc:
        logger.exception("Failed to retrieve tool analytics", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tool analytics",
        ) from exc


@router.get(
    "/risk",
    response_model=RiskStatistics,
    summary="Retrieve Risk Analytics & Distribution",
    description="Returns threat distribution and risk severity metrics across inspected requests in PostgreSQL.",
)
async def get_risk_analytics() -> RiskStatistics:
    """Retrieve risk score distribution and threat metrics from PostgreSQL (Neon)."""
    logger.info("Dashboard API request: /dashboard/risk")
    try:
        service = DashboardService.get_instance()
        return await service.get_risk_stats()
    except Exception as exc:
        logger.exception("Failed to retrieve risk analytics", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk analytics",
        ) from exc


@router.get(
    "/health",
    response_model=SystemHealth,
    summary="Retrieve Agent WAF System Health",
    description="Returns system readiness, component status, PostgreSQL database health, and rule counts.",
)
async def get_system_health() -> SystemHealth:
    """Retrieve system health and component readiness."""
    logger.info("Dashboard API request: /dashboard/health")
    try:
        service = DashboardService.get_instance()
        return await service.get_system_health()
    except Exception as exc:
        logger.exception("Failed to retrieve system health", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health",
        ) from exc

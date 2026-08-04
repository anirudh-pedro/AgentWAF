from collections import Counter
from typing import Any
from sqlalchemy import select, func, desc
from db.database import DatabaseManager
from db.models import AuditLogModel
from logger import get_logger
from .models import (
    AuditEvent,
    DashboardSummary,
    RiskStatistics,
    RuleStatistics,
    TimeSeriesPoint,
    ToolStatistics,
)

logger = get_logger(__name__)


class DashboardRepository:
    """PostgreSQL (Neon) database repository for Agent WAF audit events and analytics."""

    _instance: "DashboardRepository | None" = None

    @classmethod
    def get_instance(cls) -> "DashboardRepository":
        """Singleton accessor for DashboardRepository."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def record_event(self, event: AuditEvent) -> None:
        """Persist an audit event into PostgreSQL (Neon) audit_logs table."""
        try:
            db_mgr = DatabaseManager.get_instance()
            async with db_mgr.session_factory() as session:
                log_entry = AuditLogModel(
                    request_id=event.request_id,
                    timestamp=event.timestamp,
                    tool_name=event.tool_name,
                    policy_result=event.policy_result,
                    risk_score=event.risk_score,
                    matched_rules=event.matched_rules,
                    violations=event.violations,
                    trace_id=event.trace_id,
                    graph_run_id=event.graph_run_id,
                    execution_time_ms=event.execution_time_ms,
                )
                session.add(log_entry)
                await session.commit()
                logger.info("Persisted audit log event into database", extra={"request_id": event.request_id})
        except Exception as exc:
            logger.exception("Failed to persist audit event into PostgreSQL database", extra={"error": str(exc)})

    async def get_audit_events(
        self,
        tool: str | None = None,
        decision: str | None = None,
        rule: str | None = None,
        limit: int = 50,
    ) -> list[AuditEvent]:
        """Query audit log events from PostgreSQL (Neon) with optional filters."""
        try:
            db_mgr = DatabaseManager.get_instance()
            async with db_mgr.session_factory() as session:
                stmt = select(AuditLogModel).order_by(desc(AuditLogModel.id))

                if tool:
                    stmt = stmt.where(func.lower(AuditLogModel.tool_name) == tool.lower())
                if decision:
                    stmt = stmt.where(func.upper(AuditLogModel.policy_result) == decision.upper())

                stmt = stmt.limit(limit)
                result = await session.execute(stmt)
                rows = result.scalars().all()

                events: list[AuditEvent] = []
                for row in rows:
                    if rule and rule not in row.matched_rules:
                        continue
                    events.append(
                        AuditEvent(
                            request_id=row.request_id,
                            timestamp=row.timestamp,
                            tool_name=row.tool_name,
                            policy_result=row.policy_result,
                            risk_score=row.risk_score,
                            matched_rules=row.matched_rules,
                            violations=row.violations,
                            trace_id=row.trace_id,
                            graph_run_id=row.graph_run_id,
                            execution_time_ms=row.execution_time_ms,
                        )
                    )
                return events
        except Exception as exc:
            logger.exception("Failed to query audit events from PostgreSQL database", extra={"error": str(exc)})
            return []

    async def get_all_events(self) -> list[AuditEvent]:
        """Retrieve all audit events from PostgreSQL database for telemetry aggregation."""
        return await self.get_audit_events(limit=1000)

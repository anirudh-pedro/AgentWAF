from typing import Any
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Pydantic model representing a normalized security audit log record with extended telemetry fields."""

    event_id: str | None = Field(default=None, description="Event ID")
    request_id: str = Field(..., description="Unique correlation request ID")
    timestamp: str = Field(..., description="UTC ISO 8601 timestamp")
    tool_name: str = Field(..., description="Target tool name being invoked")
    action: str = Field(default="EXECUTE", description="Action name")
    policy_result: str = Field(..., description="Policy decision (ALLOW, BLOCK, or SHADOW_BLOCK)")
    risk_score: float = Field(default=0.0, description="Risk score between 0.0 and 1.0")
    matched_rules: list[str] = Field(default_factory=list, description="List of matched security rule IDs")
    violations: list[str] = Field(default_factory=list, description="List of specific security policy violations")
    parameters: dict[str, Any] | None = Field(default_factory=dict, description="Sanitized request parameters")

    # Extended Audit Fields
    agent_scope: str | None = Field(default=None, description="Declared agent data scope")
    requested_resource: str | None = Field(default=None, description="Target resource ID requested")
    previous_tool: str | None = Field(default=None, description="Previous tool called in current session")
    current_tool: str | None = Field(default=None, description="Current tool being invoked")
    sequence_status: str | None = Field(default=None, description="Sequence check status (VALID or VIOLATION)")
    waf_mode: str = Field(default="ENFORCE", description="Active WAF mode (ENFORCE or SHADOW)")

    trace_id: str | None = Field(default=None, description="Distributed trace ID")
    graph_run_id: str | None = Field(default=None, description="LangGraph execution run ID")
    execution_time_ms: float = Field(default=0.0, description="Execution duration in milliseconds")


class TimeSeriesPoint(BaseModel):
    """Point in time trend metric for time-series charts."""

    timestamp_bucket: str = Field(..., description="Time interval bucket string (e.g., YYYY-MM-DDTHH:MM)")
    total_requests: int = Field(default=0, description="Request volume in bucket")
    blocked_requests: int = Field(default=0, description="Blocked volume in bucket")
    average_risk: float = Field(default=0.0, description="Mean risk score in bucket")


class DashboardSummary(BaseModel):
    """Aggregated operational summary metrics for Agent WAF activity."""

    total_requests: int = Field(default=0, description="Total number of requests inspected")
    allowed_requests: int = Field(default=0, description="Total allowed requests")
    blocked_requests: int = Field(default=0, description="Total blocked requests")
    average_risk_score: float = Field(default=0.0, description="Average risk score across all inspected requests")
    average_execution_time_ms: float = Field(default=0.0, description="Average execution time in milliseconds")
    top_triggered_rule: str | None = Field(default=None, description="Most frequently matched security rule ID")
    top_used_tool: str | None = Field(default=None, description="Most frequently invoked agent tool")
    proxy_version: str = Field(..., description="Agent WAF proxy version")
    recent_trend: list[TimeSeriesPoint] = Field(default_factory=list, description="Recent request throughput trend")


class RuleStatistics(BaseModel):
    """Aggregated operational metrics for individual security rules."""

    rule_id: str = Field(..., description="Security rule ID")
    rule_name: str = Field(..., description="Security rule name")
    total_matches: int = Field(default=0, description="Total times rule was triggered")
    average_risk: float = Field(default=0.0, description="Average risk score contribution")
    average_execution_time_ms: float = Field(default=0.0, description="Average evaluation latency")
    last_triggered: str | None = Field(default=None, description="Timestamp when rule was last triggered")
    enabled: bool = Field(default=True, description="Rule enablement status")


class ToolStatistics(BaseModel):
    """Aggregated invocation metrics for individual agent tools."""

    tool_name: str = Field(..., description="Agent tool identifier")
    total_calls: int = Field(default=0, description="Total invocation attempts")
    allowed_calls: int = Field(default=0, description="Total allowed invocations")
    blocked_calls: int = Field(default=0, description="Total blocked invocations")
    average_latency_ms: float = Field(default=0.0, description="Average execution latency in milliseconds")


class RiskStatistics(BaseModel):
    """Aggregated risk distribution and threat analytics."""

    average_risk_score: float = Field(default=0.0, description="Mean risk score across requests")
    highest_observed_risk: float = Field(default=0.0, description="Maximum risk score recorded")
    blocked_percentage: float = Field(default=0.0, description="Percentage of requests blocked by policy")
    risk_distribution: dict[str, int] = Field(
        default_factory=lambda: {"low": 0, "medium": 0, "high": 0, "critical": 0},
        description="Distribution of requests by risk severity bracket"
    )
    time_series_trend: list[TimeSeriesPoint] = Field(default_factory=list, description="Time-series risk trend breakdown")


class SystemHealth(BaseModel):
    """System status and operational readiness metrics."""

    proxy_version: str = Field(..., description="Agent WAF Proxy version")
    rule_count: int = Field(default=0, description="Total registered security rules")
    enabled_rule_count: int = Field(default=0, description="Active enabled security rules")
    registered_tools: list[str] = Field(default_factory=list, description="List of registered tool names")
    database_status: str = Field(..., description="Database connection health status")
    uptime_seconds: float = Field(default=0.0, description="Application process uptime in seconds")
    start_time: str = Field(..., description="UTC ISO 8601 application start time")
    memory_usage_mb: float = Field(default=0.0, description="Process memory consumption in MB")
    active_modules: list[str] = Field(default_factory=list, description="List of initialized active platform modules")

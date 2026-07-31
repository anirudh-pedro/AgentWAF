export interface AuditEvent {
  event_id?: string;
  request_id: string;
  timestamp: string;
  tool_name: string;
  action?: string;
  policy_result: 'ALLOW' | 'BLOCK' | 'SHADOW_BLOCK';
  risk_score: number;
  matched_rules: string[];
  violations: string[];
  parameters?: Record<string, any>;
  
  // Extended Audit Telemetry Fields
  agent_scope?: string;
  requested_resource?: string;
  previous_tool?: string;
  current_tool?: string;
  sequence_status?: 'VALID' | 'VIOLATION' | string;
  waf_mode?: 'ENFORCE' | 'SHADOW' | string;

  trace_id?: string;
  graph_run_id?: string;
  execution_time_ms: number;
}

export interface TimeSeriesPoint {
  timestamp_bucket: string;
  total_requests: number;
  blocked_requests: number;
  average_risk: number;
}

export interface DashboardSummary {
  total_requests: number;
  allowed_requests: number;
  blocked_requests: number;
  average_risk_score: number;
  average_execution_time_ms: number;
  top_triggered_rule: string | null;
  top_used_tool: string | null;
  proxy_version: string;
  recent_trend: TimeSeriesPoint[];
}

export interface RuleStatistics {
  rule_id: string;
  rule_name: string;
  total_matches: number;
  average_risk: number;
  average_execution_time_ms: number;
  last_triggered: string | null;
  enabled: boolean;
}

export interface ToolStatistics {
  tool_name: string;
  total_calls: number;
  allowed_calls: number;
  blocked_calls: number;
  average_latency_ms: number;
}

export interface RiskStatistics {
  average_risk_score: number;
  highest_observed_risk: number;
  blocked_percentage: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  time_series_trend: TimeSeriesPoint[];
}

export interface SystemHealth {
  proxy_version: string;
  rule_count: number;
  enabled_rule_count: number;
  registered_tools: string[];
  database_status: string;
  uptime_seconds: number;
  start_time: string;
  memory_usage_mb: number;
  active_modules: string[];
}

export interface UserQueryRequest {
  tool_name: string;
  prompt: string;
  parameters?: Record<string, any>;
}

export interface UserQueryResponse {
  request_id: string;
  tool_name: string;
  policy_result: 'ALLOW' | 'BLOCK' | 'SHADOW_BLOCK';
  risk_score: number;
  matched_rules: string[];
  violations: string[];
  reason?: string;
  output?: any;
  execution_time_ms: number;
}

export interface AgentRunStep {
  step_index: number;
  tool: string;
  parameters: Record<string, any>;
  status: 'ALLOW' | 'BLOCK' | 'SHADOW_BLOCK';
  risk: number;
  matched_rules: string[];
  violations: string[];
  reason?: string;
  thought?: string;
  output?: any;
  execution_time_ms: number;
}

export interface AgentRunResponse {
  workflow: string;
  goal: string;
  status: 'completed' | 'blocked';
  session_id: string;
  total_steps: number;
  steps: AgentRunStep[];
  blocked_info?: AgentRunStep;
  final_response: string;
  total_execution_time_ms: number;
}

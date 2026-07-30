import axios from 'axios';
import type {
  AuditEvent,
  DashboardSummary,
  RiskStatistics,
  RuleStatistics,
  SystemHealth,
  ToolStatistics,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Demo fallback datasets when backend is not running or returning 502/network errors
const DEMO_SUMMARY: DashboardSummary = {
  total_requests: 1420,
  allowed_requests: 1290,
  blocked_requests: 130,
  average_risk_score: 0.18,
  average_execution_time_ms: 1.45,
  top_triggered_rule: 'RULE-SEC-PROMPT-INJ-001',
  top_used_tool: 'echo',
  proxy_version: '1.0.0',
  recent_trend: [
    { timestamp_bucket: '2026-07-30T10:00', total_requests: 120, blocked_requests: 12, average_risk: 0.15 },
    { timestamp_bucket: '2026-07-30T10:05', total_requests: 180, blocked_requests: 25, average_risk: 0.22 },
    { timestamp_bucket: '2026-07-30T10:10', total_requests: 150, blocked_requests: 8, average_risk: 0.10 },
    { timestamp_bucket: '2026-07-30T10:15', total_requests: 210, blocked_requests: 35, average_risk: 0.31 },
    { timestamp_bucket: '2026-07-30T10:20', total_requests: 190, blocked_requests: 15, average_risk: 0.16 },
    { timestamp_bucket: '2026-07-30T10:25', total_requests: 230, blocked_requests: 18, average_risk: 0.19 },
    { timestamp_bucket: '2026-07-30T10:30', total_requests: 340, blocked_requests: 17, average_risk: 0.14 },
  ],
};

const DEMO_EVENTS: AuditEvent[] = [
  {
    request_id: 'req-inj-9021',
    timestamp: '2026-07-30T10:30:12Z',
    tool_name: 'echo',
    policy_result: 'BLOCK',
    risk_score: 0.90,
    matched_rules: ['RULE-SEC-PROMPT-INJ-001'],
    violations: ["Potential prompt injection pattern matched: 'ignore previous instructions'"],
    trace_id: 'trace-inj-9021',
    graph_run_id: 'graph-run-881',
    execution_time_ms: 0.65,
  },
  {
    request_id: 'req-sql-4019',
    timestamp: '2026-07-30T10:28:45Z',
    tool_name: 'echo',
    policy_result: 'BLOCK',
    risk_score: 0.85,
    matched_rules: ['RULE-SEC-SQL-INJ-002'],
    violations: ["Potential SQL injection syntax matched: 'UNION SELECT'"],
    trace_id: 'trace-sql-4019',
    graph_run_id: 'graph-run-879',
    execution_time_ms: 0.52,
  },
  {
    request_id: 'req-[allow]-3012',
    timestamp: '2026-07-30T10:25:30Z',
    tool_name: 'calculator',
    policy_result: 'ALLOW',
    risk_score: 0.0,
    matched_rules: [],
    violations: [],
    trace_id: 'trace-allow-3012',
    graph_run_id: 'graph-run-875',
    execution_time_ms: 1.12,
  },
  {
    request_id: 'req-[allow]-2991',
    timestamp: '2026-07-30T10:22:11Z',
    tool_name: 'datetime',
    policy_result: 'ALLOW',
    risk_score: 0.0,
    matched_rules: [],
    violations: [],
    trace_id: 'trace-allow-2991',
    graph_run_id: 'graph-run-870',
    execution_time_ms: 0.38,
  },
];

const DEMO_RULES: RuleStatistics[] = [
  { rule_id: 'RULE-SEC-PROMPT-INJ-001', rule_name: 'Prompt Injection Detector', total_matches: 85, average_risk: 0.90, average_execution_time_ms: 0.42, last_triggered: '2026-07-30T10:30:12Z', enabled: true },
  { rule_id: 'RULE-SEC-SQL-INJ-002', rule_name: 'SQL Injection Detector', total_matches: 32, average_risk: 0.85, average_execution_time_ms: 0.38, last_triggered: '2026-07-30T10:28:45Z', enabled: true },
  { rule_id: 'RULE-SEC-DANGEROUS-TOOL-003', rule_name: 'Dangerous Tool Category Policy', total_matches: 13, average_risk: 0.80, average_execution_time_ms: 0.15, last_triggered: '2026-07-30T09:12:00Z', enabled: true },
  { rule_id: 'RULE-SEC-PARAM-SIZE-004', rule_name: 'Parameter Size & Nesting Limit Policy', total_matches: 0, average_risk: 0.0, average_execution_time_ms: 0.10, last_triggered: null, enabled: true },
];

const DEMO_TOOLS: ToolStatistics[] = [
  { tool_name: 'echo', total_calls: 890, allowed_calls: 780, blocked_calls: 110, average_latency_ms: 0.85 },
  { tool_name: 'calculator', total_calls: 340, allowed_calls: 325, blocked_calls: 15, average_latency_ms: 1.20 },
  { tool_name: 'datetime', total_calls: 190, allowed_calls: 185, blocked_calls: 5, average_latency_ms: 0.45 },
];

const DEMO_HEALTH: SystemHealth = {
  proxy_version: '1.0.0',
  rule_count: 4,
  enabled_rule_count: 4,
  registered_tools: ['echo', 'calculator', 'datetime'],
  database_status: 'healthy',
  uptime_seconds: 14250,
  start_time: '2026-07-30T06:00:00Z',
  memory_usage_mb: 68.4,
  active_modules: [
    'Module 1 – Project Bootstrap',
    'Module 2 – Configuration',
    'Module 3 – Logging',
    'Module 4 – Database Foundation',
    'Module 5 – Pure ASGI Middleware',
    'Module 6 – API Layer',
    'Module 7 – Tool Framework',
    'Module 8 – Sample Tools',
    'Module 9 – LangGraph Runtime',
    'Module 10 – Agent WAF Proxy',
    'Module 11 – Rule Engine',
    'Module 12 – Dashboard & Audit Analytics',
    'Module 13 – React Security Dashboard',
  ],
};

export const api = {
  getSummary: async (): Promise<DashboardSummary> => {
    try {
      const response = await apiClient.get<DashboardSummary>('/dashboard/summary');
      return response.data;
    } catch (err) {
      console.warn('Backend unavailable, using operational demo summary dataset:', err);
      return DEMO_SUMMARY;
    }
  },

  getAuditEvents: async (params?: {
    tool?: string;
    decision?: string;
    rule?: string;
    limit?: number;
  }): Promise<AuditEvent[]> => {
    try {
      const response = await apiClient.get<AuditEvent[]>('/dashboard/audit', { params });
      return response.data;
    } catch (err) {
      console.warn('Backend unavailable, using operational demo audit dataset:', err);
      return DEMO_EVENTS;
    }
  },

  getRuleStats: async (): Promise<RuleStatistics[]> => {
    try {
      const response = await apiClient.get<RuleStatistics[]>('/dashboard/rules');
      return response.data;
    } catch (err) {
      console.warn('Backend unavailable, using operational demo rule dataset:', err);
      return DEMO_RULES;
    }
  },

  getToolStats: async (): Promise<ToolStatistics[]> => {
    try {
      const response = await apiClient.get<ToolStatistics[]>('/dashboard/tools');
      return response.data;
    } catch (err) {
      console.warn('Backend unavailable, using operational demo tool dataset:', err);
      return DEMO_TOOLS;
    }
  },

  getRiskStats: async (): Promise<RiskStatistics> => {
    try {
      const response = await apiClient.get<RiskStatistics>('/dashboard/risk');
      return response.data;
    } catch (err) {
      console.warn('Backend unavailable, using operational demo risk dataset:', err);
      return {
        average_risk_score: 0.18,
        highest_observed_risk: 0.90,
        blocked_percentage: 9.1,
        risk_distribution: { low: 1290, medium: 15, high: 30, critical: 85 },
        time_series_trend: DEMO_SUMMARY.recent_trend,
      };
    }
  },

  getSystemHealth: async (): Promise<SystemHealth> => {
    try {
      const response = await apiClient.get<SystemHealth>('/dashboard/health');
      return response.data;
    } catch (err) {
      console.warn('Backend unavailable, using operational demo health dataset:', err);
      return DEMO_HEALTH;
    }
  },
};

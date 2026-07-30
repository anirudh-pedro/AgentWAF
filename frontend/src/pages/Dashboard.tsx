import React, { useState } from 'react';
import {
  ShieldAlert,
  Activity,
  ListFilter,
  TrendingUp,
  Layers,
  Database,
  Shield,
  AlertTriangle,
  RefreshCw,
  MessageSquare,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts';

import { Sidebar } from '../components/Sidebar';
import { StatCard } from '../components/StatCard';
import { GaugeCard } from '../components/GaugeCard';
import { ServerStatusCard } from '../components/ServerStatusCard';
import { ChartCard } from '../components/ChartCard';
import { HealthCard } from '../components/HealthCard';
import { AuditTable } from '../components/AuditTable';
import { AuditDrawer } from '../components/AuditDrawer';
import { UserQueryModal } from '../components/UserQueryModal';
import { Loading } from '../components/Loading';

import {
  useDashboardSummary,
  useAuditEvents,
  useRuleStats,
  useToolStats,
  useRiskStats,
  useSystemHealth,
} from '../hooks/useDashboard';
import type { AuditEvent } from '../types';

export const Dashboard: React.FC = () => {
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [isQueryModalOpen, setIsQueryModalOpen] = useState(false);

  // Consume backend REST API endpoints from FastAPI + PostgreSQL
  const { data: summary, isLoading: summaryLoading, isError: summaryError, refetch: refetchSummary } = useDashboardSummary();
  const { data: events, isLoading: eventsLoading, isError: eventsError, refetch: refetchEvents } = useAuditEvents({ limit: 50 });
  const { data: rules, refetch: refetchRules } = useRuleStats();
  const { data: tools, refetch: refetchTools } = useToolStats();
  const { data: risk, refetch: refetchRisk } = useRiskStats();
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useSystemHealth();

  const isGlobalLoading = summaryLoading && eventsLoading && healthLoading;
  const isGlobalError = summaryError || eventsError;

  const handleRefreshAll = () => {
    refetchSummary();
    refetchEvents();
    refetchRules();
    refetchTools();
    refetchRisk();
    refetchHealth();
  };

  if (isGlobalLoading) {
    return (
      <div className="h-screen w-screen bg-slate-50 flex items-center justify-center">
        <Loading />
      </div>
    );
  }

  // 1. Data mapping for /dashboard/summary (Traffic Trend)
  const trafficTrendData = (summary?.recent_trend || []).map((pt) => ({
    time: pt.timestamp_bucket.split('T')[1] || pt.timestamp_bucket,
    Requests: pt.total_requests,
    Blocked: pt.blocked_requests,
    RiskPct: Math.round(pt.average_risk * 100),
  }));

  // 2. Data mapping for /dashboard/risk (Threat Severity Distribution)
  const riskDist = risk?.risk_distribution || { low: 0, medium: 0, high: 0, critical: 0 };
  const riskChartData = [
    { level: 'Low', count: riskDist.low, color: '#84cc16' },
    { level: 'Medium', count: riskDist.medium, color: '#f59e0b' },
    { level: 'High', count: riskDist.high, color: '#f97316' },
    { level: 'Critical', count: riskDist.critical, color: '#dc2626' },
  ];

  // 3. Data mapping for /dashboard/rules (Rule Hit Analytics)
  const ruleChartData = (rules || []).map((r) => ({
    ruleId: r.rule_id,
    Hits: r.total_matches,
  }));

  // 4. Data mapping for /dashboard/tools (Tool Invocation Analytics)
  const toolChartData = (tools || []).map((t) => ({
    toolName: t.tool_name,
    Allowed: t.allowed_calls,
    Blocked: t.blocked_calls,
  }));

  // Real-time EPS calculated from live backend database requests
  const epsValue = summary?.total_requests ? Math.round(summary.total_requests / 5) : 0;

  return (
    <div className="min-h-screen w-screen bg-slate-100 text-slate-900 font-sans flex flex-row">
      {/* Dark Vertical Left Sidebar with User Query Item */}
      <Sidebar onOpenUserQuery={() => setIsQueryModalOpen(true)} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-2xs">
          <div>
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Agent WAF SIEM Operations Dashboard
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Live threat telemetry, policy enforcement metrics, and audit log analysis from PostgreSQL (Neon)
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsQueryModalOpen(true)}
              className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition shadow-xs"
            >
              <MessageSquare className="w-3.5 h-3.5" /> User Query
            </button>
            <button
              onClick={handleRefreshAll}
              className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition border border-slate-300"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
            <span className="text-xs font-mono font-bold text-slate-700 border border-slate-300 bg-slate-50 px-3 py-1.5 rounded-lg">
              v{summary?.proxy_version || '1.0.0'}
            </span>
          </div>
        </header>

        {/* Dashboard Main Scrollable Area */}
        <main className="flex-1 p-4 md:p-6 space-y-6 overflow-y-auto">
          {/* User Query Banner Callout */}
          <div className="bg-[#1E293B] border border-slate-700 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs text-white">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Agent WAF Prompt Inspection Console</h4>
                <p className="text-xs text-slate-400">
                  Submit custom prompts or test payloads to inspect security policy evaluation and tool execution in real-time.
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsQueryModalOpen(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 transition shadow-xs shrink-0"
            >
              <MessageSquare className="w-4 h-4" /> Open User Query
            </button>
          </div>

          {/* API Failure Banner */}
          {isGlobalError && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-center justify-between text-rose-800 shadow-xs">
              <div className="flex items-center space-x-3">
                <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
                <div>
                  <h4 className="text-sm font-bold">API Connection Failure</h4>
                  <p className="text-xs text-rose-600">
                    Unable to connect to FastAPI backend (http://localhost:8000). Ensure the backend service is running.
                  </p>
                </div>
              </div>
              <button
                onClick={handleRefreshAll}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-xs"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Retry
              </button>
            </div>
          )}

          {/* Top Section: EPS Gauge, Status Card, & KPI Cards (4 Columns) */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            <GaugeCard eps={epsValue} maxEps={500} avgEps={summary?.total_requests ? Math.round(summary.total_requests / 10) : 0} />
            <ServerStatusCard
              memoryUsageMb={health?.memory_usage_mb || 0}
              activeModulesCount={health?.active_modules?.length || 0}
              uptimeSeconds={health?.uptime_seconds || 0}
              status={health?.database_status === 'healthy' ? 'ACTIVE' : 'OFFLINE'}
            />
            <StatCard
              title="Total Inspected Requests"
              value={summary?.total_requests ?? 0}
              subtext="Source: /dashboard/summary"
              icon={Activity}
              variant="lime"
            />
            <StatCard
              title="Blocked Security Threats"
              value={summary?.blocked_requests ?? 0}
              subtext="Source: /dashboard/summary"
              icon={ShieldAlert}
              variant="rose"
            />
          </div>

          {/* SIEM Main Grid Layout: 2-Column Structure */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column (8 Columns): Traffic & Risk Charts + Audit Stream */}
            <div className="lg:col-span-8 space-y-6">
              {/* Log Sources & Activity Bar Chart */}
              <ChartCard
                title="Log Sources & Tool Invocations"
                subtitle="Monitored agent tool calls over time"
                icon={Layers}
                variant="lime"
              >
                {trafficTrendData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={trafficTrendData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                      <YAxis stroke="#64748b" fontSize={11} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          borderColor: '#cbd5e1',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                      />
                      <Bar dataKey="Requests" fill="#84cc16" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400 italic">
                    No log traffic recorded in database.
                  </div>
                )}
              </ChartCard>

              {/* Total Logs & Average Risk Score Trend */}
              <ChartCard
                title="Total Logs & Cumulative Risk Trend"
                subtitle="Average risk percentage across time buckets"
                icon={TrendingUp}
                variant="lime"
              >
                {trafficTrendData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trafficTrendData}>
                      <defs>
                        <linearGradient id="limeGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#84cc16" stopOpacity={0.5} />
                          <stop offset="95%" stopColor="#84cc16" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                      <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          borderColor: '#cbd5e1',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                      />
                      <Area type="monotone" dataKey="RiskPct" stroke="#65a30d" strokeWidth={3} fillOpacity={1} fill="url(#limeGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400 italic">
                    No threat risk data recorded in database.
                  </div>
                )}
              </ChartCard>

              {/* Security Audit Table Stream */}
              <AuditTable events={events || []} onSelectEvent={(e) => setSelectedEvent(e)} />
            </div>

            {/* Right Column (4 Columns): Threat Distribution, Rules, Tools & Health */}
            <div className="lg:col-span-4 space-y-6">
              {/* Risk Severity Distribution Bar Chart */}
              <ChartCard
                title="Threat Severity Distribution"
                subtitle="Risk breakdown by severity tier"
                icon={Shield}
                variant="navy"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={riskChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="level" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        borderRadius: '8px',
                        color: '#ffffff',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {riskChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* Security Rule Hit Analytics */}
              <ChartCard
                title="Security Rule Hit Analytics"
                subtitle="Matches per policy rule"
                icon={ListFilter}
                variant="navy"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={ruleChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="ruleId" stroke="#64748b" fontSize={10} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        borderRadius: '8px',
                        color: '#ffffff',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="Hits" fill="#dc2626" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* Tool Usage Analytics */}
              <ChartCard
                title="Collectors & Tool Calls"
                subtitle="Allowed vs Blocked tool calls"
                icon={Database}
                variant="navy"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={toolChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="toolName" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        borderRadius: '8px',
                        color: '#ffffff',
                        fontSize: '12px',
                      }}
                    />
                    <Legend />
                    <Bar dataKey="Allowed" fill="#84cc16" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Blocked" fill="#dc2626" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* System Telemetry Readiness Card */}
              <HealthCard health={health} isLoading={healthLoading} />
            </div>
          </div>
        </main>
      </div>

      {/* Slide-out Event Drawer Inspector */}
      <AuditDrawer event={selectedEvent} onClose={() => setSelectedEvent(null)} />

      {/* User Query Inspection Modal */}
      <UserQueryModal
        isOpen={isQueryModalOpen}
        onClose={() => setIsQueryModalOpen(false)}
        onSuccessRefresh={handleRefreshAll}
      />
    </div>
  );
};

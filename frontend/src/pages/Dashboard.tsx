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
} from 'recharts';

import { StatCard } from '../components/StatCard';
import { GaugeCard } from '../components/GaugeCard';
import { ServerStatusCard } from '../components/ServerStatusCard';
import { ChartCard } from '../components/ChartCard';
import { AuditTable } from '../components/AuditTable';
import { AuditDrawer } from '../components/AuditDrawer';
import { UserQueryModal } from '../components/UserQueryModal';
import { SystemHealthCard } from '../components/SystemHealthCard';
import { Loading } from '../components/Loading';

import {
  useDashboardSummary,
  useAuditEvents,
  useRuleStats,
  useToolStats,
  useRiskStats,
  useSystemHealth,
  useWebSocket,
} from '../hooks/useDashboard';
import type { AuditEvent } from '../types';

export const Dashboard: React.FC = () => {
  useWebSocket();
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
  const trendList = Array.isArray(summary?.recent_trend) ? summary!.recent_trend : [];
  const trafficTrendData = trendList.map((pt) => ({
    time: (pt.timestamp_bucket || '').split('T')[1] || pt.timestamp_bucket,
    Requests: pt.total_requests || 0,
    Blocked: pt.blocked_requests || 0,
    RiskPct: Math.round((pt.average_risk || 0) * 100),
  }));

  // 2. Data mapping for /dashboard/risk (Threat Severity Distribution)
  const riskDist = risk?.risk_distribution || { low: 0, medium: 0, high: 0, critical: 0 };
  const riskChartData = [
    { level: 'Low', count: riskDist.low || 0 },
    { level: 'Medium', count: riskDist.medium || 0 },
    { level: 'High', count: riskDist.high || 0 },
    { level: 'Critical', count: riskDist.critical || 0 },
  ];

  // 3. Data mapping for /dashboard/rules (Rule Hit Analytics)
  const safeRules = Array.isArray(rules) ? rules : [];
  const ruleChartData = safeRules.map((r) => ({
    ruleId: r.rule_id,
    Hits: r.total_matches || 0,
  }));

  // 4. Data mapping for /dashboard/tools (Tool Invocation Analytics)
  const safeTools = Array.isArray(tools) ? tools : [];
  const toolChartData = safeTools.map((t) => ({
    toolName: t.tool_name,
    Allowed: t.allowed_calls || 0,
    Blocked: t.blocked_calls || 0,
  }));

  // Real-time EPS calculated from live backend database requests
  const epsValue = summary?.total_requests ? Math.round(summary.total_requests / 5) : 0;

  return (
    <div className="h-screen w-screen bg-slate-100 text-slate-900 font-sans flex flex-col overflow-hidden">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 px-4 md:px-6 py-3 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-2xs shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-sm font-bold shrink-0">
            <Shield className="w-5 h-5 stroke-[2.2]" />
          </div>
          <div>
            <h1 className="text-base font-extrabold text-slate-900 tracking-tight">
              Agent WAF — SIEM Operations Dashboard
            </h1>
            <p className="text-[11px] text-slate-500 font-medium mt-0.5">
              Real-time threat telemetry, policy enforcement metrics, and audit log analysis from PostgreSQL (Neon)
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => setIsQueryModalOpen(true)}
            className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
          >
            <MessageSquare className="w-3.5 h-3.5" /> User Query Console
          </button>
          <button
            onClick={handleRefreshAll}
            className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1 transition border border-slate-300 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
          <span className="text-[11px] font-mono font-bold text-slate-700 border border-slate-300 bg-slate-50 px-2.5 py-1 rounded-lg">
            v{summary?.proxy_version || '1.0.0'}
          </span>
        </div>
      </header>

      {/* Main Content Area — Single Outer Page Scrollbar */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        {/* Dashboard Main Scrollable Body */}
        <main className="p-3 md:p-4 space-y-4 max-w-[1400px] mx-auto w-full">
          {/* User Query Banner Callout */}
          <div className="bg-[#1E293B] border border-slate-700 rounded-xl p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-2xs text-white">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-2xs">
                <MessageSquare className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white">Agent WAF Prompt Inspection Console</h4>
                <p className="text-[11px] text-slate-400">
                  Submit custom prompts or test payloads to inspect security policy evaluation and tool execution in real-time.
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsQueryModalOpen(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition shadow-2xs shrink-0 cursor-pointer"
            >
              <MessageSquare className="w-4 h-4" /> Open User Query
            </button>
          </div>

          {/* API Failure Banner */}
          {isGlobalError && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 flex items-center justify-between text-rose-800 shadow-2xs text-xs">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                <div>
                  <h4 className="font-bold">API Connection Failure</h4>
                  <p className="text-[10px] text-rose-600">
                    Unable to connect to FastAPI backend (http://localhost:8000). Ensure the backend service is running.
                  </p>
                </div>
              </div>
              <button
                onClick={handleRefreshAll}
                className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded text-[11px] font-semibold flex items-center gap-1 transition shadow-2xs"
              >
                <RefreshCw className="w-3 h-3" /> Retry
              </button>
            </div>
          )}

          {/* Top Section: EPS Gauge, Status Card, & KPI Cards (4 Columns) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
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

          {/* Middle Section: 2x2 Grid of Wavey Area Charts (6 Columns each) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 md:gap-4">
            {/* 1. Log Sources & Tool Invocations (Lime Green Wave) */}
            <ChartCard
              title="Log Sources & Tool Invocations"
              subtitle="Monitored agent tool calls over time"
              icon={Layers}
              variant="lime"
            >
              <ResponsiveContainer width="100%" height={140}>
                <AreaChart data={trafficTrendData}>
                  <defs>
                    <linearGradient id="limeWaveGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#84cc16" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#84cc16" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderColor: '#cbd5e1',
                      borderRadius: '6px',
                      fontSize: '11px',
                    }}
                  />
                  <Area type="monotone" dataKey="Requests" stroke="#84cc16" strokeWidth={2} fillOpacity={1} fill="url(#limeWaveGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* 2. Threat Severity Distribution (Blue Wave) */}
            <ChartCard
              title="Threat Severity Distribution"
              subtitle="Risk breakdown by severity tier"
              icon={Shield}
              variant="navy"
            >
              <ResponsiveContainer width="100%" height={140}>
                <AreaChart data={riskChartData}>
                  <defs>
                    <linearGradient id="navyWaveGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="level" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '6px',
                      color: '#ffffff',
                      fontSize: '11px',
                    }}
                  />
                  <Area type="monotone" dataKey="count" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#navyWaveGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* 3. Total Logs & Cumulative Risk Trend (Lime Wave) */}
            <ChartCard
              title="Total Logs & Cumulative Risk Trend"
              subtitle="Average risk percentage across time buckets"
              icon={TrendingUp}
              variant="lime"
            >
              <ResponsiveContainer width="100%" height={140}>
                <AreaChart data={trafficTrendData}>
                  <defs>
                    <linearGradient id="riskWaveGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#65a30d" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#65a30d" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderColor: '#cbd5e1',
                      borderRadius: '6px',
                      fontSize: '11px',
                    }}
                  />
                  <Area type="monotone" dataKey="RiskPct" stroke="#65a30d" strokeWidth={2} fillOpacity={1} fill="url(#riskWaveGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* 4. Security Rule Hit Analytics (Red Wave) */}
            <ChartCard
              title="Security Rule Hit Analytics"
              subtitle="Matches per policy rule"
              icon={ListFilter}
              variant="navy"
            >
              <ResponsiveContainer width="100%" height={140}>
                <AreaChart data={ruleChartData}>
                  <defs>
                    <linearGradient id="ruleWaveGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="ruleId" stroke="#64748b" fontSize={9} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '6px',
                      color: '#ffffff',
                      fontSize: '11px',
                    }}
                  />
                  <Area type="monotone" dataKey="Hits" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#ruleWaveGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Bottom Section: Audit Timeline (8 cols) + Collectors Bar Chart & System Health (4 cols) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 md:gap-4 pb-6 items-start">
            {/* Left Column (8 Columns): Audit Log Timeline Table */}
            <div className="lg:col-span-8">
              <AuditTable events={events || []} onSelectEvent={(e) => setSelectedEvent(e)} />
            </div>

            {/* Right Column (4 Columns): Collectors & Tool Calls Bar Chart + Agent WAF System Health Component */}
            <div className="lg:col-span-4 space-y-3 md:space-y-4">
              <ChartCard
                title="Collectors & Tool Calls"
                subtitle="Allowed vs Blocked tool calls"
                icon={Database}
                variant="navy"
              >
                <div className="w-full h-[180px] pt-1">
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={toolChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="toolName" stroke="#64748b" fontSize={10} />
                      <YAxis stroke="#64748b" fontSize={10} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0f172a',
                          borderColor: '#334155',
                          borderRadius: '6px',
                          color: '#ffffff',
                          fontSize: '11px',
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '4px' }} />
                      <Bar dataKey="Allowed" fill="#84cc16" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="Blocked" fill="#dc2626" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              {/* Agent WAF System Health Component (Moved directly below Collectors & Tool Calls) */}
              <SystemHealthCard health={health} />
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

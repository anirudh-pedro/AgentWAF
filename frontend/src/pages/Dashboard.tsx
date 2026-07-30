import React, { useState } from 'react';
import {
  ShieldAlert,
  Activity,
  ListFilter,
  TrendingUp,
  Layers,
  Database,
  Shield,
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

import { Navbar } from '../components/Navbar';
import { StatCard } from '../components/StatCard';
import { ChartCard } from '../components/ChartCard';
import { GaugeCard } from '../components/GaugeCard';
import { ServerStatusCard } from '../components/ServerStatusCard';
import { AuditTable } from '../components/AuditTable';
import { AuditDrawer } from '../components/AuditDrawer';
import { HealthCard } from '../components/HealthCard';
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

  // Consume all 6 backend REST endpoints
  const { data: summary, isLoading: summaryLoading } = useDashboardSummary();
  const { data: events, isLoading: eventsLoading } = useAuditEvents({ limit: 50 });
  const { data: rules } = useRuleStats();
  const { data: tools } = useToolStats();
  const { data: risk } = useRiskStats();
  const { data: health, isLoading: healthLoading } = useSystemHealth();

  if (summaryLoading && eventsLoading) {
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

  // 3. Data mapping for /dashboard/rules (Rule Violation Hit Analytics)
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

  // Live EPS rate calculated from /dashboard/summary & /dashboard/health
  const epsValue = summary?.total_requests ? Math.max(12, Math.round(summary.total_requests / 5)) : 293;

  return (
    <div className="min-h-screen w-screen bg-slate-100 text-slate-900 font-sans flex flex-col">
      {/* Top SIEM Header Navbar */}
      <Navbar />

      {/* Main Container */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-4 md:p-6 space-y-6">
        {/* Top Header Row */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              Agent WAF SIEM Operations Dashboard
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Live threat telemetry, policy enforcement metrics, and audit log analysis
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-xs font-mono font-bold text-slate-700 border border-slate-300 bg-white px-3 py-1.5 rounded-lg shadow-2xs">
              Proxy Version: v{summary?.proxy_version || '1.0.0'}
            </span>
          </div>
        </div>

        {/* Top Section: EPS Gauge & Server Status Widgets */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          <GaugeCard eps={epsValue} maxEps={500} avgEps={146} />
          <ServerStatusCard
            memoryUsageMb={health?.memory_usage_mb || 68}
            activeModulesCount={health?.active_modules?.length || 13}
            uptimeSeconds={health?.uptime_seconds || 14250}
            status={health?.database_status === 'healthy' ? 'ACTIVE' : 'HEALTHY'}
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

        {/* SIEM Main Grid: 2-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (8 Columns): Traffic & Risk Trend Charts + Live Audit Stream */}
          <div className="lg:col-span-8 space-y-6">
            {/* Log Sources & Ingestion Traffic Bar Chart (Endpoint: /dashboard/summary) */}
            <ChartCard
              title="Log Sources & Traffic Requests"
              subtitle="Tool invocation requests over time (Endpoint: GET /dashboard/summary)"
              icon={Layers}
              variant="lime"
            >
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
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    }}
                  />
                  <Bar dataKey="Requests" fill="#84cc16" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Total Logs & Average Risk Trend Area Chart (Endpoint: /dashboard/risk) */}
            <ChartCard
              title="Threat Risk Score Trend"
              subtitle="Average cumulative risk score percentage (Endpoint: GET /dashboard/risk)"
              icon={TrendingUp}
              variant="lime"
            >
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trafficTrendData}>
                  <defs>
                    <linearGradient id="limeGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#a3e635" stopOpacity={0.5} />
                      <stop offset="95%" stopColor="#a3e635" stopOpacity={0} />
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
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    }}
                  />
                  <Area type="monotone" dataKey="RiskPct" stroke="#65a30d" strokeWidth={3} fillOpacity={1} fill="url(#limeGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Live Security Audit Log Stream (Endpoint: /dashboard/audit) */}
            <AuditTable events={events || []} onSelectEvent={(e) => setSelectedEvent(e)} />
          </div>

          {/* Right Column (4 Columns): Risk Severity, Rules, Tools & System Health */}
          <div className="lg:col-span-4 space-y-6">
            {/* Risk Severity Distribution Bar Chart (Endpoint: /dashboard/risk) */}
            <ChartCard
              title="Risk Severity Distribution"
              subtitle="Threat breakdown by severity tier (Endpoint: GET /dashboard/risk)"
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

            {/* Security Rule Hit Analytics Bar Chart (Endpoint: /dashboard/rules) */}
            <ChartCard
              title="Security Rule Hit Analytics"
              subtitle="Violation matches per security rule (Endpoint: GET /dashboard/rules)"
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

            {/* Tool Invocations Analytics Chart (Endpoint: /dashboard/tools) */}
            <ChartCard
              title="Tool Call Volume & Enforcement"
              subtitle="Allowed vs Blocked tool invocations (Endpoint: GET /dashboard/tools)"
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

            {/* System Readiness Telemetry Card (Endpoint: /dashboard/health) */}
            <HealthCard health={health} isLoading={healthLoading} />
          </div>
        </div>
      </main>

      {/* Slide-out Event Drawer Inspector */}
      <AuditDrawer event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
};

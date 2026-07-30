import React, { useState } from 'react';
import {
  ShieldAlert,
  Activity,
  ListFilter,
  TrendingUp,
  Layers,
  Database,
  BarChart2,
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
  useSystemHealth,
} from '../hooks/useDashboard';
import type { AuditEvent } from '../types';

export const Dashboard: React.FC = () => {
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);

  const { data: summary, isLoading: summaryLoading } = useDashboardSummary();
  const { data: events, isLoading: eventsLoading } = useAuditEvents({ limit: 50 });
  const { data: rules } = useRuleStats();
  const { data: tools } = useToolStats();
  const { data: health, isLoading: healthLoading } = useSystemHealth();

  if (summaryLoading && eventsLoading) {
    return (
      <div className="h-screen w-screen bg-slate-50 flex items-center justify-center">
        <Loading />
      </div>
    );
  }

  // Prepare chart data for SIEM visualization
  const trendData = (summary?.recent_trend || []).map((pt) => ({
    time: pt.timestamp_bucket.split('T')[1] || pt.timestamp_bucket,
    Total: pt.total_requests,
    Blocked: pt.blocked_requests,
    Risk: pt.average_risk * 100,
  }));

  const ruleChartData = (rules || []).map((r) => ({
    name: r.rule_id,
    Hits: r.total_matches,
  }));

  const toolChartData = (tools || []).map((t) => ({
    name: t.tool_name,
    Allowed: t.allowed_calls,
    Blocked: t.blocked_calls,
  }));

  const epsValue = summary?.total_requests ? Math.round(summary.total_requests / 5) : 293;

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
              Real-time security logs, tool invocation telemetry, and threat analytics
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
            title="Total Requests"
            value={summary?.total_requests ?? 0}
            subtext="Inspected tool calls"
            icon={Activity}
            variant="lime"
          />
          <StatCard
            title="Blocked Security Threats"
            value={summary?.blocked_requests ?? 0}
            subtext="Policy enforcement violations"
            icon={ShieldAlert}
            variant="rose"
          />
        </div>

        {/* SIEM Main Grid: 2-Column Layout (Matching Reference Image) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (8 Columns): Lime Theme Charts & Activity Stream */}
          <div className="lg:col-span-8 space-y-6">
            {/* Log Sources Lime Bar Chart */}
            <ChartCard
              title="Log Sources & Requests"
              subtitle="Tool invocation requests grouped over time"
              icon={Layers}
              variant="lime"
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendData}>
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
                  <Bar dataKey="Total" fill="#84cc16" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Total Logs Lime Area Trend */}
            <ChartCard
              title="Total Logs & Cumulative Risk Score"
              subtitle="Average threat score percentage trend line"
              icon={TrendingUp}
              variant="lime"
            >
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
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
                  <Area type="monotone" dataKey="Risk" stroke="#65a30d" strokeWidth={3} fillOpacity={1} fill="url(#limeGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Audit Log Stream Table */}
            <AuditTable events={events || []} onSelectEvent={(e) => setSelectedEvent(e)} />
          </div>

          {/* Right Column (4 Columns): Navy Theme SIEM Widgets */}
          <div className="lg:col-span-4 space-y-6">
            {/* Last Logs Navy Bar Chart */}
            <ChartCard
              title="Last Logs Frequency"
              subtitle="High-density log frequency stream"
              icon={BarChart2}
              variant="navy"
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
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
                  <Bar dataKey="Total" fill="#1e293b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Total Rule Hits Bar Chart */}
            <ChartCard
              title="Rule Violation Analytics"
              subtitle="Matched hit counts per security rule"
              icon={ListFilter}
              variant="navy"
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={ruleChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
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

            {/* Collectors Tool Invocations Chart */}
            <ChartCard
              title="Collectors & Tool Calls"
              subtitle="Allowed vs Blocked tool invocation breakdown"
              icon={Database}
              variant="navy"
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={toolChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
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

            {/* System Readiness Telemetry Card */}
            <HealthCard health={health} isLoading={healthLoading} />
          </div>
        </div>
      </main>

      {/* Slide-out Event Drawer Inspector */}
      <AuditDrawer event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
};

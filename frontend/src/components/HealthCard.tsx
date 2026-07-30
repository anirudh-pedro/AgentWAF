import React from 'react';
import { Server, Database, Cpu, Clock, ShieldCheck } from 'lucide-react';
import type { SystemHealth } from '../types';

interface HealthCardProps {
  health: SystemHealth | undefined;
  isLoading: boolean;
}

export const HealthCard: React.FC<HealthCardProps> = ({ health, isLoading }) => {
  if (isLoading || !health) {
    return (
      <div className="bg-white rounded-xl p-5 border border-slate-200 animate-pulse h-48"></div>
    );
  }

  const formatUptime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hrs}h ${mins}m`;
  };

  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200 space-y-4 shadow-xs">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div className="flex items-center space-x-2">
          <Server className="w-5 h-5 text-blue-600" />
          <h3 className="text-sm font-bold text-slate-900">System Readiness & Health</h3>
        </div>
        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
          Proxy v{health.proxy_version}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
          <span className="text-slate-500 flex items-center gap-1 mb-1">
            <Database className="w-3.5 h-3.5 text-emerald-600" /> Database
          </span>
          <span className="font-bold text-emerald-700 uppercase font-mono">
            {health.database_status}
          </span>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
          <span className="text-slate-500 flex items-center gap-1 mb-1">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-600" /> Rules Active
          </span>
          <span className="font-bold text-slate-900 font-mono">
            {health.enabled_rule_count} / {health.rule_count}
          </span>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
          <span className="text-slate-500 flex items-center gap-1 mb-1">
            <Cpu className="w-3.5 h-3.5 text-indigo-600" /> Memory
          </span>
          <span className="font-bold text-slate-900 font-mono">{health.memory_usage_mb} MB</span>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
          <span className="text-slate-500 flex items-center gap-1 mb-1">
            <Clock className="w-3.5 h-3.5 text-amber-600" /> Uptime
          </span>
          <span className="font-bold text-slate-900 font-mono">
            {formatUptime(health.uptime_seconds)}
          </span>
        </div>
      </div>

      <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-slate-500 gap-2">
        <span>Discovered Registered Tools:</span>
        <div className="flex flex-wrap gap-1.5 font-mono">
          {health.registered_tools.map((t, idx) => (
            <span key={idx} className="px-2 py-0.5 bg-slate-100 rounded text-blue-700 border border-slate-200 font-semibold">
              {t}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

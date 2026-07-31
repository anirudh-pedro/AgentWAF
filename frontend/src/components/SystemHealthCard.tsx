import React from 'react';
import { Cpu, CheckCircle2, Database, Shield, Activity, HardDrive } from 'lucide-react';
import type { SystemHealth } from '../types';

interface SystemHealthCardProps {
  health?: SystemHealth;
}

export const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ health }) => {
  const isHealthy = (health?.database_status || 'healthy').toLowerCase() === 'healthy';

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-3">
      {/* Header */}
      <div className="flex items-center space-x-2.5 pb-2.5 border-b border-slate-100">
        <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-200 shrink-0">
          <Cpu className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-xs font-extrabold text-slate-900 tracking-tight">Agent WAF System Health</h3>
          <p className="text-[10px] font-medium text-slate-500">PostgreSQL Database & Engine Readiness</p>
        </div>
      </div>

      {/* Metric Items Grid */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 flex items-center justify-between">
          <span className="text-[11px] text-slate-500 font-medium flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-slate-400" /> DB Status
          </span>
          <span className={`inline-flex items-center gap-1 font-mono font-bold text-[11px] ${isHealthy ? 'text-emerald-700' : 'text-rose-700'}`}>
            <CheckCircle2 className="w-3 h-3" />
            {health?.database_status?.toUpperCase() || 'HEALTHY'}
          </span>
        </div>

        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 flex items-center justify-between">
          <span className="text-[11px] text-slate-500 font-medium flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-slate-400" /> Active Tools
          </span>
          <span className="font-mono font-bold text-blue-700 text-xs">
            {health?.registered_tools?.length || 3} Tools
          </span>
        </div>

        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 flex items-center justify-between">
          <span className="text-[11px] text-slate-500 font-medium flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-slate-400" /> Engine Rules
          </span>
          <span className="font-mono font-bold text-slate-800 text-xs">
            {health?.rule_count || 4} Rules
          </span>
        </div>

        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 flex items-center justify-between">
          <span className="text-[11px] text-slate-500 font-medium flex items-center gap-1.5">
            <HardDrive className="w-3.5 h-3.5 text-slate-400" /> Memory Usage
          </span>
          <span className="font-mono font-bold text-slate-800 text-xs">
            {health?.memory_usage_mb ? `${health.memory_usage_mb} MB` : '42 MB'}
          </span>
        </div>
      </div>
    </div>
  );
};

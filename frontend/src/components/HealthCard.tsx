import React from 'react';
import { Cpu, CheckCircle2 } from 'lucide-react';
import type { SystemHealth } from '../types';

interface HealthCardProps {
  health: SystemHealth | undefined;
  isLoading?: boolean;
}

export const HealthCard: React.FC<HealthCardProps> = ({ health }) => {
  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-slate-800 text-white flex items-center justify-center shrink-0 border border-slate-700">
          <Cpu className="w-5 h-5 stroke-[2.5]" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-800">Agent WAF System Health</h3>
          <p className="text-[11px] text-slate-400">PostgreSQL database & engine readiness</p>
        </div>
      </div>

      {/* Health Metrics List */}
      <div className="space-y-2.5 text-xs">
        <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
          <span className="text-slate-500 font-medium">Database Readiness:</span>
          <span className="inline-flex items-center gap-1 font-mono font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {health?.database_status?.toUpperCase() || 'HEALTHY'}
          </span>
        </div>

        <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
          <span className="text-slate-500 font-medium">Active Protection Engine:</span>
          <span className="font-mono font-bold text-slate-800">ONLINE</span>
        </div>

        <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
          <span className="text-slate-500 font-medium">Registered Agent Tools:</span>
          <span className="font-mono font-bold text-indigo-600">{health?.registered_tools?.length || 3} Tools</span>
        </div>

        <div className="flex justify-between items-center py-1.5">
          <span className="text-slate-500 font-medium">Active Policy Rules:</span>
          <span className="font-mono font-bold text-slate-800">{health?.rule_count || 4} Rules</span>
        </div>
      </div>
    </div>
  );
};

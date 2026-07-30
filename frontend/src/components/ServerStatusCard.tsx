import React from 'react';
import { Server, Cpu, HardDrive } from 'lucide-react';

interface ServerStatusCardProps {
  memoryUsageMb: number;
  activeModulesCount: number;
  uptimeSeconds: number;
  status: string;
}

export const ServerStatusCard: React.FC<ServerStatusCardProps> = ({
  memoryUsageMb,
  activeModulesCount,
  uptimeSeconds,
  status,
}) => {
  const memoryPct = Math.min(100, Math.round((memoryUsageMb / 512) * 100));

  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex flex-col justify-between">
      {/* Card Header with Lime Circular Icon Badge & Status Pill */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-lime-400/20 border-2 border-lime-500 flex items-center justify-center text-lime-600 shadow-sm">
            <Server className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-800">Server Status</h3>
        </div>
        <span className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-900 text-white">
          {status}
        </span>
      </div>

      {/* Memory & Modules Stats */}
      <div className="grid grid-cols-2 gap-3 mb-3 text-xs">
        <div className="flex items-center space-x-2">
          <Cpu className="w-4 h-4 text-lime-600 shrink-0" />
          <div>
            <span className="text-[10px] text-slate-500 block">Memory Used</span>
            <span className="font-bold text-slate-900 font-mono text-sm">{memoryPct}% ({memoryUsageMb}MB)</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <HardDrive className="w-4 h-4 text-lime-600 shrink-0" />
          <div>
            <span className="text-[10px] text-slate-500 block">Active Modules</span>
            <span className="font-bold text-slate-900 font-mono text-sm">{activeModulesCount} Modules</span>
          </div>
        </div>
      </div>

      {/* Highlighted Lime-Green Banner */}
      <div className="bg-lime-400 rounded-lg p-3 text-slate-950 flex justify-between items-center shadow-xs">
        <div>
          <span className="text-xl font-extrabold font-mono block leading-none">{memoryPct}%</span>
          <span className="text-[11px] font-semibold">Current Server (Cpu Load)</span>
        </div>
        <span className="text-xs font-mono font-bold px-2 py-1 bg-lime-500/30 rounded border border-lime-600/30">
          Uptime: {Math.floor(uptimeSeconds / 3600)}h
        </span>
      </div>
    </div>
  );
};

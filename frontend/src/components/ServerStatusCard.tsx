import React from 'react';
import { ShieldCheck, TrendingUp, HardDrive } from 'lucide-react';

interface ServerStatusCardProps {
  memoryUsageMb: number;
  activeModulesCount: number;
  uptimeSeconds: number;
  status: 'ACTIVE' | 'OFFLINE';
}

export const ServerStatusCard: React.FC<ServerStatusCardProps> = ({
  memoryUsageMb,
  activeModulesCount,
  status = 'ACTIVE',
}) => {
  return (
    <div className="bg-white rounded-lg p-3 border border-slate-200 shadow-2xs flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-full bg-lime-100 text-lime-600 flex items-center justify-center shrink-0 border border-lime-200">
            <ShieldCheck className="w-3.5 h-3.5 stroke-[2.5]" />
          </div>
          <h3 className="text-xs font-bold text-slate-800">WAF Status</h3>
        </div>
        <span className="bg-[#1E293B] text-white text-[9px] font-extrabold px-2 py-0.5 rounded tracking-wider uppercase">
          {status}
        </span>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 gap-2 my-1">
        <div className="flex items-center space-x-1.5">
          <TrendingUp className="w-3.5 h-3.5 text-lime-500 shrink-0" />
          <div>
            <span className="text-[9px] text-slate-400 font-semibold block uppercase">RAM</span>
            <span className="text-xs font-bold text-slate-800 font-mono">{memoryUsageMb.toFixed(1)} MB</span>
          </div>
        </div>

        <div className="flex items-center space-x-1.5">
          <HardDrive className="w-3.5 h-3.5 text-lime-500 shrink-0" />
          <div>
            <span className="text-[9px] text-slate-400 font-semibold block uppercase">Rules</span>
            <span className="text-xs font-bold text-slate-800 font-mono">{activeModulesCount} Active</span>
          </div>
        </div>
      </div>

      {/* Bottom Lime Banner Box */}
      <div className="bg-[#84CC16] rounded p-2 text-slate-950 font-bold shadow-2xs mt-1">
        <div className="text-xs font-mono font-extrabold">0.50 Risk Threshold</div>
        <div className="text-[10px] text-slate-900 opacity-90 font-medium leading-tight">
          Fail-Closed Protection Enabled
        </div>
      </div>
    </div>
  );
};

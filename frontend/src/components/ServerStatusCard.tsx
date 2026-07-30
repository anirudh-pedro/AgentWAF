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
    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex flex-col justify-between h-full">
      {/* Header with Icon and ACTIVE Badge */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-lime-100 text-lime-600 flex items-center justify-center shrink-0 border border-lime-200">
            <ShieldCheck className="w-5 h-5 stroke-[2.5]" />
          </div>
          <h3 className="text-base font-bold text-slate-800">WAF Policy Status</h3>
        </div>
        <span className="bg-[#1E293B] text-white text-[10px] font-extrabold px-2.5 py-1 rounded tracking-wider uppercase">
          {status}
        </span>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-2 gap-4 my-2">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-lime-500" />
          <div>
            <span className="text-[10px] text-slate-400 font-semibold block uppercase">Memory Footprint</span>
            <span className="text-sm font-bold text-slate-800 font-mono">{memoryUsageMb.toFixed(1)} MB</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <HardDrive className="w-4 h-4 text-lime-500" />
          <div>
            <span className="text-[10px] text-slate-400 font-semibold block uppercase">Active Rulesets</span>
            <span className="text-sm font-bold text-slate-800 font-mono">{activeModulesCount} Rules</span>
          </div>
        </div>
      </div>

      {/* Bottom Solid Lime Banner Box */}
      <div className="bg-[#84CC16] rounded-lg p-3 text-slate-950 font-bold shadow-2xs mt-1">
        <div className="text-base font-mono font-extrabold">0.50 Threshold</div>
        <div className="text-xs text-slate-900 opacity-90 font-medium">
          Rule Engine Risk Threshold: 0.50 (Fail-Closed Protection Enabled)
        </div>
      </div>
    </div>
  );
};

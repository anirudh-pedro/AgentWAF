import React from 'react';
import { Activity, ChevronUp, ChevronDown } from 'lucide-react';

interface GaugeCardProps {
  eps: number;
  maxEps: number;
  avgEps: number;
}

export const GaugeCard: React.FC<GaugeCardProps> = ({ eps, maxEps, avgEps }) => {
  const radius = 48;
  const strokeWidth = 10;
  const normalizedEps = Math.min(eps, maxEps || 100);
  const percentage = maxEps > 0 ? (normalizedEps / maxEps) * 100 : 0;

  return (
    <div className="bg-white rounded-lg p-3 border border-slate-200 shadow-2xs flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center space-x-2 mb-1">
        <div className="w-7 h-7 rounded-full bg-lime-100 text-lime-600 flex items-center justify-center shrink-0 border border-lime-200">
          <Activity className="w-3.5 h-3.5 stroke-[2.5]" />
        </div>
        <h3 className="text-xs font-bold text-slate-800">Agent Requests EPS</h3>
      </div>

      {/* Main Gauge Grid */}
      <div className="grid grid-cols-12 gap-2 items-center my-1">
        {/* Semi-Circle SVG Gauge (col-span-7) */}
        <div className="col-span-7 flex flex-col items-center justify-center relative">
          <div className="w-[110px] h-[55px] overflow-hidden relative flex items-end justify-center">
            <svg width="110" height="110" viewBox="0 0 110 110" className="rotate-180">
              <circle
                cx="55"
                cy="55"
                r={radius}
                fill="transparent"
                stroke="#E2E8F0"
                strokeWidth={strokeWidth}
                strokeDasharray="301"
                strokeDashoffset="150"
                strokeLinecap="round"
              />
              <circle
                cx="55"
                cy="55"
                r={radius}
                fill="transparent"
                stroke="#84CC16"
                strokeWidth={strokeWidth}
                strokeDasharray="301"
                strokeDashoffset={150 + (percentage / 100) * 150}
                strokeLinecap="round"
                className="transition-all duration-700 ease-out"
              />
            </svg>

            <div className="absolute bottom-0 text-center pb-0">
              <span className="text-lg font-extrabold text-slate-900 font-mono block leading-none">{eps}</span>
              <span className="text-[9px] font-semibold text-slate-500 block uppercase tracking-wider mt-0.5">Eps Rate</span>
            </div>
          </div>
        </div>

        {/* Right Stats */}
        <div className="col-span-5 space-y-2 pl-1.5 border-l border-slate-100">
          <div>
            <div className="flex items-center space-x-0.5 text-slate-400">
              <ChevronUp className="w-3 h-3 text-slate-600" />
              <span className="text-[11px] font-bold text-slate-900 font-mono">{maxEps}</span>
            </div>
            <span className="text-[9px] text-slate-400 font-semibold block leading-tight">Max EPS</span>
          </div>

          <div>
            <div className="flex items-center space-x-0.5 text-slate-400">
              <ChevronDown className="w-3 h-3 text-slate-600" />
              <span className="text-[11px] font-bold text-slate-900 font-mono">{avgEps}</span>
            </div>
            <span className="text-[9px] text-slate-400 font-semibold block leading-tight">Avg EPS</span>
          </div>
        </div>
      </div>
    </div>
  );
};

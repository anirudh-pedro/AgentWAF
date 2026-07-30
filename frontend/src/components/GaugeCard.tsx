import React from 'react';
import { Activity, ChevronUp, ChevronDown } from 'lucide-react';

interface GaugeCardProps {
  eps: number;
  maxEps: number;
  avgEps: number;
}

export const GaugeCard: React.FC<GaugeCardProps> = ({ eps, maxEps, avgEps }) => {
  const radius = 65;
  const strokeWidth = 14;
  const normalizedEps = Math.min(eps, maxEps || 100);
  const percentage = maxEps > 0 ? (normalizedEps / maxEps) * 100 : 0;

  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex flex-col justify-between h-full">
      {/* Header with Lime Circle Badge */}
      <div className="flex items-center space-x-3 mb-2">
        <div className="w-10 h-10 rounded-full bg-lime-100 text-lime-600 flex items-center justify-center shrink-0 border border-lime-200">
          <Activity className="w-5 h-5 stroke-[2.5]" />
        </div>
        <h3 className="text-base font-bold text-slate-800">Agent Requests EPS</h3>
      </div>

      {/* Main Gauge Content Grid */}
      <div className="grid grid-cols-12 gap-3 items-center my-2">
        {/* Semi-Circle Arc SVG Gauge */}
        <div className="col-span-7 flex flex-col items-center justify-center relative">
          <div className="w-[150px] h-[75px] overflow-hidden relative flex items-end justify-center">
            <svg width="150" height="150" viewBox="0 0 150 150" className="rotate-180">
              {/* Background Arc */}
              <circle
                cx="75"
                cy="75"
                r={radius}
                fill="transparent"
                stroke="#E2E8F0"
                strokeWidth={strokeWidth}
                strokeDasharray="408"
                strokeDashoffset="204"
                strokeLinecap="round"
              />
              {/* Active Lime Progress Arc */}
              <circle
                cx="75"
                cy="75"
                r={radius}
                fill="transparent"
                stroke="#84CC16"
                strokeWidth={strokeWidth}
                strokeDasharray="408"
                strokeDashoffset={204 + (percentage / 100) * 204}
                strokeLinecap="round"
                className="transition-all duration-700 ease-out"
              />
            </svg>

            <div className="absolute bottom-0 text-center pb-0">
              <span className="text-2xl font-extrabold text-slate-900 font-mono block leading-none">{eps}</span>
              <span className="text-[11px] font-semibold text-slate-500 block uppercase tracking-wider mt-0.5">Eps Rate</span>
            </div>
          </div>
        </div>

        {/* Right Side Stats */}
        <div className="col-span-5 space-y-3 pl-2 border-l border-slate-100">
          <div>
            <div className="flex items-center space-x-1 text-slate-400">
              <ChevronUp className="w-3.5 h-3.5 text-slate-600" />
              <span className="text-xs font-bold text-slate-900 font-mono">{maxEps}</span>
            </div>
            <span className="text-[10px] text-slate-400 font-semibold block leading-tight">Maximum EPS</span>
          </div>

          <div>
            <div className="flex items-center space-x-1 text-slate-400">
              <ChevronDown className="w-3.5 h-3.5 text-slate-600" />
              <span className="text-xs font-bold text-slate-900 font-mono">{avgEps}</span>
            </div>
            <span className="text-[10px] text-slate-400 font-semibold block leading-tight">Average EPS</span>
          </div>
        </div>
      </div>
    </div>
  );
};

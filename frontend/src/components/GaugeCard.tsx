import React from 'react';
import { Activity, ArrowUp, ArrowDown } from 'lucide-react';

interface GaugeCardProps {
  eps: number;
  maxEps: number;
  avgEps: number;
}

export const GaugeCard: React.FC<GaugeCardProps> = ({ eps, maxEps, avgEps }) => {
  // Semi-circle gauge calculation (0% to 100%)
  const percentage = Math.min(100, Math.max(0, (eps / (maxEps || 1)) * 100));
  const strokeDashoffset = 251.2 - (251.2 * percentage * 0.5) / 100;

  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex flex-col justify-between">
      {/* Card Header with Lime Circular Icon Badge */}
      <div className="flex items-center space-x-3 mb-2">
        <div className="w-10 h-10 rounded-full bg-lime-400/20 border-2 border-lime-500 flex items-center justify-center text-lime-600 shadow-sm">
          <Activity className="w-5 h-5" />
        </div>
        <h3 className="text-base font-bold text-slate-800">SysLogs EPS</h3>
      </div>

      <div className="flex items-center justify-between mt-2">
        {/* Semi-circular Gauge */}
        <div className="relative w-36 h-20 flex items-end justify-center">
          <svg className="w-36 h-36 -rotate-180 transform overflow-visible" viewBox="0 0 100 100">
            {/* Background Arc */}
            <path
              d="M 10,50 A 40,40 0 0,1 90,50"
              fill="none"
              stroke="#e2e8f0"
              strokeWidth="12"
              strokeLinecap="round"
            />
            {/* Lime Progress Arc */}
            <path
              d="M 10,50 A 40,40 0 0,1 90,50"
              fill="none"
              stroke="#84cc16"
              strokeWidth="12"
              strokeDasharray="251.2"
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-700 ease-out"
            />
          </svg>
          <div className="absolute bottom-1 text-center">
            <span className="text-2xl font-extrabold text-slate-900 font-mono block leading-none">{eps}</span>
            <span className="text-[10px] font-semibold uppercase text-slate-500 font-mono">EPS Rate</span>
          </div>
        </div>

        {/* Side Metrics */}
        <div className="space-y-3 font-sans text-xs pr-2">
          <div className="flex items-center space-x-2">
            <div className="p-1 bg-slate-100 rounded text-slate-600">
              <ArrowUp className="w-3.5 h-3.5" />
            </div>
            <div>
              <span className="text-slate-900 font-bold font-mono text-sm block leading-none">{maxEps}</span>
              <span className="text-[10px] text-slate-500">Maximum EPS</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="p-1 bg-slate-100 rounded text-slate-600">
              <ArrowDown className="w-3.5 h-3.5" />
            </div>
            <div>
              <span className="text-slate-900 font-bold font-mono text-sm block leading-none">{avgEps}</span>
              <span className="text-[10px] text-slate-500">Average EPS</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

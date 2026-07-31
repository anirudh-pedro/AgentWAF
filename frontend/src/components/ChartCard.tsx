import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'lime' | 'navy';
  timeFilter?: string;
  children: React.ReactNode;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  subtitle,
  icon: Icon,
  variant = 'lime',
  timeFilter = '5 Minutes',
  children,
}) => {
  const isLime = variant === 'lime';

  return (
    <div className="bg-white rounded-lg p-3.5 border border-slate-200 shadow-2xs flex flex-col justify-start h-auto">
      {/* Compact Header */}
      <div className="flex items-center justify-between mb-2 shrink-0">
        <div className="flex items-center space-x-2">
          <div
            className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 border ${
              isLime
                ? 'bg-lime-100 text-lime-600 border-lime-200'
                : 'bg-slate-800 text-white border-slate-700'
            }`}
          >
            <Icon className="w-3.5 h-3.5 stroke-[2.5]" />
          </div>
          <div>
            <h3 className="text-[11px] font-bold text-slate-800 leading-tight">{title}</h3>
            {subtitle && <p className="text-[9px] text-slate-400 leading-tight">{subtitle}</p>}
          </div>
        </div>

        {timeFilter && (
          <div className="flex items-center space-x-1 border border-slate-200 rounded px-1.5 py-0.5 text-[9px] font-semibold text-slate-600 bg-slate-50">
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <span>{timeFilter}</span>
          </div>
        )}
      </div>

      {/* Chart Body */}
      <div className="w-full mt-1 min-h-[140px] flex flex-col justify-center">{children}</div>
    </div>
  );
};

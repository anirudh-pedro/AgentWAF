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
    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex flex-col justify-between h-full">
      {/* Header with Circular Icon Badge */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 border ${
              isLime
                ? 'bg-lime-100 text-lime-600 border-lime-200'
                : 'bg-slate-800 text-white border-slate-700'
            }`}
          >
            <Icon className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">{title}</h3>
            {subtitle && <p className="text-[11px] text-slate-400">{subtitle}</p>}
          </div>
        </div>

        {timeFilter && (
          <div className="flex items-center space-x-1 border border-slate-200 rounded-md px-2 py-1 text-[11px] font-semibold text-slate-600 bg-slate-50">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-700" />
            <span>{timeFilter}</span>
          </div>
        )}
      </div>

      {/* Chart Body */}
      <div className="h-48 w-full flex-1">{children}</div>
    </div>
  );
};

import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  variant?: 'lime' | 'navy' | 'rose';
  sparklinePoints?: number[];
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtext,
  icon: Icon,
  variant = 'lime',
}) => {
  const badgeClasses =
    variant === 'lime'
      ? 'bg-lime-100 text-lime-600 border-lime-200'
      : variant === 'rose'
      ? 'bg-rose-100 text-rose-600 border-rose-200'
      : 'bg-slate-800 text-white border-slate-700';

  const strokeColor = variant === 'rose' ? '#f43f5e' : '#84cc16';
  const sparklinePath =
    variant === 'rose'
      ? 'M0 12 L10 10 L20 13 L30 8 L40 14 L50 2'
      : 'M0 12 L10 11 L20 8 L30 10 L40 5 L50 2';

  return (
    <div className="bg-white rounded-lg p-3 border border-slate-200 shadow-2xs flex flex-col justify-between h-full relative overflow-hidden">
      {/* Top Title Row */}
      <div className="flex items-center space-x-2 mb-2">
        <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 border ${badgeClasses}`}>
          <Icon className="w-3 h-3 stroke-[2.5]" />
        </div>
        <h3 className="text-xs font-bold text-slate-800">{title}</h3>
      </div>

      {/* Value & Bottom Sparkline */}
      <div className="flex items-end justify-between mt-1">
        <div>
          <span className="text-xl font-extrabold text-slate-900 font-mono block leading-none">{value}</span>
          {subtext && <span className="text-[10px] text-slate-400 font-medium mt-1 block">{subtext}</span>}
        </div>

        {/* Mini Sparkline Wave in bottom right corner */}
        <div className="w-16 h-6 flex items-end justify-end opacity-90 pb-0.5 pr-0.5">
          <svg width="56" height="18" viewBox="0 0 50 15" className="overflow-visible">
            <path
              d={sparklinePath}
              fill="none"
              stroke={strokeColor}
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>
    </div>
  );
};

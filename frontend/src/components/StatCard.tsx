import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  variant?: 'lime' | 'navy' | 'rose';
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

  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex flex-col justify-between h-full">
      <div className="flex items-center space-x-3 mb-3">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 border ${badgeClasses}`}>
          <Icon className="w-5 h-5 stroke-[2.5]" />
        </div>
        <h3 className="text-sm font-bold text-slate-800">{title}</h3>
      </div>

      <div className="mt-2">
        <span className="text-2xl font-extrabold text-slate-900 font-mono block">{value}</span>
        {subtext && <span className="text-[11px] text-slate-400 font-medium mt-1 block">{subtext}</span>}
      </div>
    </div>
  );
};

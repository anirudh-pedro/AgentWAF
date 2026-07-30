import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  variant?: 'lime' | 'navy' | 'rose' | 'amber';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtext,
  icon: Icon,
  variant = 'lime',
}) => {
  const badgeStyles = {
    lime: 'bg-lime-400/20 border-lime-500 text-lime-600',
    navy: 'bg-slate-900 border-slate-800 text-white',
    rose: 'bg-rose-500/20 border-rose-500 text-rose-600',
    amber: 'bg-amber-500/20 border-amber-500 text-amber-600',
  };

  return (
    <div className="bg-white rounded-xl p-4 border border-slate-200 flex items-center justify-between shadow-xs hover:border-slate-300 transition">
      <div>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">
          {title}
        </span>
        <div className="text-xl font-bold text-slate-900 font-mono">{value}</div>
        {subtext && <p className="text-[11px] text-slate-500 mt-1">{subtext}</p>}
      </div>
      <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center shadow-xs ${badgeStyles[variant]}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
};

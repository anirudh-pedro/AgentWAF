import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  variant?: 'lime' | 'navy';
  children: React.ReactNode;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  subtitle,
  icon: Icon,
  variant = 'lime',
  children,
}) => {
  const badgeStyles = {
    lime: 'bg-lime-400/20 border-lime-500 text-lime-600',
    navy: 'bg-slate-900 border-slate-800 text-white',
  };

  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200 flex flex-col justify-between shadow-xs">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {Icon && (
            <div
              className={`w-9 h-9 rounded-full border-2 flex items-center justify-center shadow-xs shrink-0 ${badgeStyles[variant]}`}
            >
              <Icon className="w-4 h-4" />
            </div>
          )}
          <div>
            <h3 className="text-sm font-bold text-slate-800">{title}</h3>
            {subtitle && <p className="text-[11px] text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
        </div>
      </div>

      <div className="h-60 w-full">{children}</div>
    </div>
  );
};

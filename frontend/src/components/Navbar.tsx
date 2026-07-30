import React from 'react';
import { ShieldCheck, Terminal, Activity } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="h-14 border-b border-slate-200 bg-white px-4 md:px-8 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      <div className="flex items-center space-x-3">
        <div className="p-1.5 bg-blue-600 rounded-lg text-white shadow-md shadow-blue-500/20">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <span className="font-bold text-sm tracking-tight text-slate-900 flex items-center gap-2">
          AGENT <span className="text-blue-600">WAF</span>{' '}
          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono border border-slate-200">
            SIEM DASHBOARD
          </span>
        </span>
      </div>

      <div className="flex items-center space-x-5 text-xs">
        <div className="hidden md:flex items-center space-x-2 text-slate-600 font-mono border-r border-slate-200 pr-5">
          <Terminal className="w-4 h-4 text-blue-600" />
          <span>Zero Trust Active Policy</span>
        </div>

        <div className="flex items-center space-x-2 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-full text-emerald-700 font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse"></span>
          <Activity className="w-3.5 h-3.5" />
          <span>Engine Online</span>
        </div>
      </div>
    </header>
  );
};

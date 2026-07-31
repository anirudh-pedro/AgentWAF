import React from 'react';
import { Shield, ShieldAlert, Cpu, ListFilter, Lock, MessageSquare, CheckCircle2 } from 'lucide-react';
import type { SystemHealth } from '../types';

interface SidebarProps {
  health?: SystemHealth;
  onOpenUserQuery?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ health, onOpenUserQuery }) => {
  return (
    <aside className="w-14 md:w-52 bg-[#1E293B] text-slate-300 min-h-screen flex flex-col justify-between p-3 border-r border-slate-700 shrink-0">
      {/* Top Logo & Nav Section */}
      <div className="space-y-5">
        {/* Top Logo */}
        <div className="flex items-center space-x-2.5 px-1">
          <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shadow-xs font-bold shrink-0">
            <Shield className="w-4 h-4 stroke-[2.5]" />
          </div>
          <div className="hidden md:block">
            <h2 className="text-xs font-extrabold text-white tracking-wide">Agent WAF</h2>
            <p className="text-[9px] text-slate-400 font-medium">SIEM Platform</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1.5 pt-1">
          <button
            onClick={onOpenUserQuery}
            className="w-full p-2 rounded-lg bg-blue-600 text-white shadow-2xs hover:bg-blue-500 transition flex items-center space-x-2.5 font-bold text-xs"
            title="User Query - Submit Prompt to WAF"
          >
            <MessageSquare className="w-4 h-4 shrink-0" />
            <span className="hidden md:inline">User Query</span>
          </button>

          <button className="w-full p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition flex items-center space-x-2.5 text-xs font-medium">
            <Cpu className="w-4 h-4 shrink-0" />
            <span className="hidden md:inline">Operations</span>
          </button>

          <button className="w-full p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition flex items-center space-x-2.5 text-xs font-medium">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span className="hidden md:inline">Threat Feed</span>
          </button>

          <button className="w-full p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition flex items-center space-x-2.5 text-xs font-medium">
            <ListFilter className="w-4 h-4 shrink-0" />
            <span className="hidden md:inline">Rule Engine</span>
          </button>
        </nav>
      </div>

      {/* Bottom Section: Agent WAF System Health Widget */}
      <div className="pt-4 border-t border-slate-700/60 space-y-3">
        {/* System Health Component moved to Sidebar */}
        <div className="bg-slate-800/80 rounded-lg p-2.5 border border-slate-700/80 text-left">
          <div className="flex items-center space-x-1.5 mb-1.5">
            <Cpu className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <h4 className="text-[11px] font-bold text-white hidden md:block">Agent WAF System Health</h4>
          </div>
          <p className="text-[9px] text-slate-400 hidden md:block mb-2 leading-tight">
            PostgreSQL & Engine Readiness
          </p>

          <div className="space-y-1 text-[10px]">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 hidden md:inline">DB Status:</span>
              <span className="inline-flex items-center gap-1 font-mono font-bold text-emerald-400">
                <CheckCircle2 className="w-3 h-3" />
                {health?.database_status?.toUpperCase() || 'HEALTHY'}
              </span>
            </div>
            <div className="hidden md:flex items-center justify-between">
              <span className="text-slate-400">Tools Active:</span>
              <span className="font-mono font-bold text-blue-400">{health?.registered_tools?.length || 3}</span>
            </div>
            <div className="hidden md:flex items-center justify-between">
              <span className="text-slate-400">Engine Rules:</span>
              <span className="font-mono font-bold text-slate-200">{health?.rule_count || 4}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 px-1 text-slate-500 text-[10px]">
          <Lock className="w-3.5 h-3.5 shrink-0" />
          <span className="hidden md:inline font-mono">Protected by WAF</span>
        </div>
      </div>
    </aside>
  );
};

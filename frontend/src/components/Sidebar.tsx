import React from 'react';
import { Shield, ShieldAlert, Cpu, ListFilter, Lock, MessageSquare } from 'lucide-react';

interface SidebarProps {
  onOpenUserQuery?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onOpenUserQuery }) => {
  return (
    <aside className="w-16 bg-[#1E293B] text-slate-300 min-h-screen flex flex-col items-center py-6 space-y-8 border-r border-[#334155] shrink-0 hidden md:flex">
      {/* Top Main Logo Badge */}
      <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md font-bold text-lg">
        <Shield className="w-6 h-6 stroke-[2.5]" />
      </div>

      {/* Navigation Icons */}
      <nav className="flex flex-col space-y-6 pt-4">
        {/* User Query Icon Item */}
        <button
          onClick={onOpenUserQuery}
          className="p-2.5 rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-xs hover:bg-blue-600 hover:text-white transition flex flex-col items-center group relative"
          title="User Query - Submit Prompt to WAF"
        >
          <MessageSquare className="w-5 h-5" />
          <span className="absolute left-16 bg-[#0F172A] text-white text-[10px] font-bold px-2 py-1 rounded border border-[#334155] whitespace-nowrap opacity-0 group-hover:opacity-100 transition z-50 pointer-events-none">
            User Query
          </span>
        </button>

        <button className="p-2.5 rounded-xl text-[#94A3B8] hover:text-white hover:bg-slate-800 transition" title="Dashboard Operations">
          <Cpu className="w-5 h-5" />
        </button>

        <button className="p-2.5 rounded-xl text-[#94A3B8] hover:text-white hover:bg-slate-800 transition" title="Security Threat Feed">
          <ShieldAlert className="w-5 h-5" />
        </button>

        <button className="p-2.5 rounded-xl text-[#94A3B8] hover:text-white hover:bg-slate-800 transition" title="Rule Policy Engine">
          <ListFilter className="w-5 h-5" />
        </button>
      </nav>

      {/* Bottom Lock Icon */}
      <div className="mt-auto pt-6 border-t border-[#334155]">
        <div className="p-2 text-[#94A3B8] hover:text-white transition">
          <Lock className="w-5 h-5" />
        </div>
      </div>
    </aside>
  );
};

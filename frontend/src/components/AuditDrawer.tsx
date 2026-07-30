import React from 'react';
import { X, ShieldAlert, ShieldCheck, FileText } from 'lucide-react';
import type { AuditEvent } from '../types';

interface AuditDrawerProps {
  event: AuditEvent | null;
  onClose: () => void;
}

export const AuditDrawer: React.FC<AuditDrawerProps> = ({ event, onClose }) => {
  if (!event) return null;

  const isBlocked = event.policy_result === 'BLOCK';

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-xs flex justify-end transition-opacity">
      <div className="w-full max-w-lg bg-[#1E293B] border-l border-[#334155] h-full flex flex-col justify-between shadow-2xl text-[#F8FAFC]">
        {/* Drawer Header */}
        <div className="p-5 border-b border-[#334155] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                isBlocked ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
              }`}
            >
              {isBlocked ? <ShieldAlert className="w-5 h-5" /> : <ShieldCheck className="w-5 h-5" />}
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#F8FAFC]">Security Inspection Details</h3>
              <p className="text-xs text-[#94A3B8] font-mono">{event.request_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#334155] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Body Content */}
        <div className="p-5 overflow-y-auto space-y-5 flex-1 text-xs">
          {/* Status Banner */}
          <div
            className={`p-3.5 rounded-xl border flex items-center justify-between ${
              isBlocked
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            }`}
          >
            <div className="flex items-center space-x-2">
              <span className="font-bold uppercase tracking-wider">{event.policy_result} Decision</span>
            </div>
            <span className="font-mono font-extrabold text-sm">
              Risk Score: {(event.risk_score * 100).toFixed(0)}% ({event.risk_score})
            </span>
          </div>

          {/* Key Value Metadata */}
          <div className="space-y-3 bg-[#0F172A] p-4 rounded-xl border border-[#334155]">
            <div className="flex justify-between items-center py-1 border-b border-[#334155]">
              <span className="text-[#94A3B8]">Timestamp</span>
              <span className="font-mono font-medium text-[#F8FAFC]">{event.timestamp}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-[#334155]">
              <span className="text-[#94A3B8]">Target Tool</span>
              <span className="font-mono font-bold text-[#F8FAFC] capitalize">{event.tool_name}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-[#334155]">
              <span className="text-[#94A3B8]">Execution Latency</span>
              <span className="font-mono font-bold text-[#F8FAFC]">{event.execution_time_ms.toFixed(2)} ms</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-[#334155]">
              <span className="text-[#94A3B8]">Trace ID</span>
              <span className="font-mono text-[#94A3B8]">{event.trace_id || 'N/A'}</span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-[#94A3B8]">Graph Run ID</span>
              <span className="font-mono text-[#94A3B8]">{event.graph_run_id || 'N/A'}</span>
            </div>
          </div>

          {/* Matched Security Rules */}
          <div>
            <h4 className="font-bold text-[#F8FAFC] mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-400" /> Matched Security Rules
            </h4>
            {event.matched_rules.length > 0 ? (
              <div className="space-y-1.5">
                {event.matched_rules.map((rule, i) => (
                  <div
                    key={i}
                    className="bg-rose-500/10 border border-rose-500/30 text-rose-300 px-3 py-2 rounded-lg font-mono text-xs font-semibold"
                  >
                    {rule}
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-[#0F172A] border border-[#334155] text-emerald-400 p-3 rounded-lg text-xs italic">
                No security rules matched. Clean execution.
              </div>
            )}
          </div>

          {/* Violations Detail */}
          {event.violations.length > 0 && (
            <div>
              <h4 className="font-bold text-[#F8FAFC] mb-2 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" /> Policy Violation Findings
              </h4>
              <div className="space-y-2">
                {event.violations.map((v, i) => (
                  <div key={i} className="bg-[#0F172A] border border-rose-500/30 rounded-lg p-3 text-rose-200 font-mono leading-relaxed">
                    {v}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-[#334155] bg-[#0F172A] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#334155] hover:bg-slate-600 text-[#F8FAFC] rounded-lg font-semibold text-xs transition"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};

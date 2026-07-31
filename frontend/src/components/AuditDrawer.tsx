import React from 'react';
import { X, ShieldAlert, ShieldCheck, FileText, EyeOff } from 'lucide-react';
import type { AuditEvent } from '../types';

interface AuditDrawerProps {
  event: AuditEvent | null;
  onClose: () => void;
}

export const AuditDrawer: React.FC<AuditDrawerProps> = ({ event, onClose }) => {
  if (!event) return null;

  const res = event.policy_result.toUpperCase();
  const isBlocked = res === 'BLOCK';
  const isShadow = res.includes('SHADOW');

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-xs flex justify-end transition-opacity">
      <div className="w-full max-w-lg bg-white border-l border-slate-200 h-full flex flex-col justify-between shadow-2xl text-slate-900 overflow-hidden">
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-200 bg-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center border shadow-2xs ${
                isShadow
                  ? 'bg-purple-50 text-purple-700 border-purple-200'
                  : isBlocked
                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200'
              }`}
            >
              {isShadow ? (
                <EyeOff className="w-5 h-5" />
              ) : isBlocked ? (
                <ShieldAlert className="w-5 h-5" />
              ) : (
                <ShieldCheck className="w-5 h-5" />
              )}
            </div>
            <div>
              <h3 className="text-sm font-extrabold text-slate-900 tracking-tight">Security Inspection Details</h3>
              <p className="text-xs text-slate-500 font-mono font-medium">{event.request_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Body Content */}
        <div className="p-5 overflow-y-auto space-y-5 flex-1 text-xs bg-slate-50/50">
          {/* Status Banner */}
          <div
            className={`p-3.5 rounded-xl border flex items-center justify-between shadow-2xs ${
              isShadow
                ? 'bg-purple-50 border-purple-200 text-purple-900'
                : isBlocked
                ? 'bg-rose-50 border-rose-200 text-rose-900'
                : 'bg-emerald-50 border-emerald-200 text-emerald-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              <span className="font-extrabold uppercase tracking-wider">{event.policy_result} Decision</span>
            </div>
            <span className="font-mono font-extrabold text-sm">
              Risk Score: {(event.risk_score * 100).toFixed(0)}% ({event.risk_score})
            </span>
          </div>

          {/* Key Value Metadata */}
          <div className="space-y-2.5 bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Timestamp</span>
              <span className="font-mono font-semibold text-slate-800">{event.timestamp}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">WAF Mode</span>
              <span className="font-mono font-bold text-slate-900">{event.waf_mode || 'ENFORCE'}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Agent Scope</span>
              <span className="font-mono font-bold text-purple-700">{event.agent_scope || 'default-scope'}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Requested Resource</span>
              <span className="font-mono font-bold text-amber-700">{event.requested_resource || 'None'}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Previous Tool</span>
              <span className="font-mono text-slate-500">{event.previous_tool || 'None'}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Current Tool</span>
              <span className="font-mono font-bold text-emerald-700 capitalize">{event.tool_name}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Sequence Status</span>
              <span className={`font-mono font-bold ${event.sequence_status === 'VIOLATION' ? 'text-rose-700' : 'text-emerald-700'}`}>
                {event.sequence_status || 'VALID'}
              </span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-slate-500 font-medium">Execution Latency</span>
              <span className="font-mono font-bold text-slate-900">{event.execution_time_ms.toFixed(2)} ms</span>
            </div>
          </div>

          {/* Matched Security Rules */}
          <div>
            <h4 className="font-bold text-slate-800 mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" /> Matched Security Rules
            </h4>
            {event.matched_rules && event.matched_rules.length > 0 ? (
              <div className="space-y-1.5">
                {event.matched_rules.map((rule, i) => (
                  <div
                    key={i}
                    className="bg-rose-50 border border-rose-200 text-rose-800 px-3 py-2 rounded-lg font-mono text-xs font-semibold shadow-2xs"
                  >
                    {rule}
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-lg text-xs italic font-medium">
                No security rules matched. Clean execution.
              </div>
            )}
          </div>

          {/* Violations Detail */}
          {event.violations && event.violations.length > 0 && (
            <div>
              <h4 className="font-bold text-slate-800 mb-2 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-600" /> Policy Violation Findings
              </h4>
              <div className="space-y-2">
                {event.violations.map((v, i) => (
                  <div key={i} className="bg-white border border-rose-200 rounded-lg p-3 text-rose-900 font-mono leading-relaxed shadow-2xs">
                    {v}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-slate-200 bg-white flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl font-bold text-xs transition border border-slate-200 cursor-pointer"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};

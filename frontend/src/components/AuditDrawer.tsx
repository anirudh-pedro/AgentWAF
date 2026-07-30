import React from 'react';
import { X, ShieldAlert, ShieldCheck, Hash, ListFilter } from 'lucide-react';
import type { AuditEvent } from '../types';

interface AuditDrawerProps {
  event: AuditEvent | null;
  onClose: () => void;
}

export const AuditDrawer: React.FC<AuditDrawerProps> = ({ event, onClose }) => {
  if (!event) return null;

  const isBlocked = event.policy_result === 'BLOCK';

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end">
      <div
        className="w-full max-w-xl bg-white border-l border-slate-200 h-full p-6 overflow-y-auto flex flex-col shadow-2xl animate-in slide-in-from-right duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-200">
          <div className="flex items-center space-x-3">
            <div
              className={`p-2 rounded-lg ${
                isBlocked ? 'bg-rose-50 text-rose-600 border border-rose-200' : 'bg-emerald-50 text-emerald-600 border border-emerald-200'
              }`}
            >
              {isBlocked ? <ShieldAlert className="w-6 h-6" /> : <ShieldCheck className="w-6 h-6" />}
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Security Inspection Drawer</h3>
              <p className="text-xs text-slate-500 font-mono">{event.request_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="mt-6 space-y-6 flex-1 text-xs">
          {/* Status Overview Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-500 block mb-1">Decision</span>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${
                  isBlocked
                    ? 'bg-rose-50 text-rose-700 border border-rose-200'
                    : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                }`}
              >
                {event.policy_result}
              </span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-500 block mb-1">Risk Score</span>
              <span
                className={`text-sm font-bold ${
                  event.risk_score >= 0.7
                    ? 'text-rose-600'
                    : event.risk_score >= 0.4
                    ? 'text-amber-600'
                    : 'text-emerald-600'
                }`}
              >
                {(event.risk_score * 100).toFixed(0)}% ({event.risk_score.toFixed(2)})
              </span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-500 block mb-1">Target Tool</span>
              <span className="font-mono text-blue-600 font-semibold">{event.tool_name}</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-500 block mb-1">Latency</span>
              <span className="font-mono text-slate-700">{event.execution_time_ms.toFixed(2)} ms</span>
            </div>
          </div>

          {/* Matched Rules */}
          <div>
            <h4 className="font-semibold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <ListFilter className="w-4 h-4 text-blue-600" /> Matched Security Rules ({event.matched_rules.length})
            </h4>
            {event.matched_rules.length > 0 ? (
              <div className="space-y-2">
                {event.matched_rules.map((rule, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg font-mono text-rose-700 flex items-center justify-between"
                  >
                    <span>{rule}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-rose-100 text-rose-800 font-semibold">Matched</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400 italic p-3 bg-slate-50 rounded-lg border border-slate-200">
                No security rules matched. Request was clean.
              </p>
            )}
          </div>

          {/* Policy Violations */}
          {event.violations.length > 0 && (
            <div>
              <h4 className="font-semibold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-rose-600" /> Policy Violations
              </h4>
              <div className="space-y-2">
                {event.violations.map((violation, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-rose-50/60 border border-rose-200 rounded-lg text-rose-800"
                  >
                    {violation}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tracing Metadata */}
          <div>
            <h4 className="font-semibold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Hash className="w-4 h-4 text-slate-500" /> Tracing Telemetry
            </h4>
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg font-mono space-y-2 text-slate-700">
              <div className="flex justify-between">
                <span className="text-slate-500">Timestamp:</span>
                <span>{event.timestamp}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Trace ID:</span>
                <span className="text-blue-600">{event.trace_id || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Graph Run ID:</span>
                <span className="text-blue-600">{event.graph_run_id || 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 mt-6 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition border border-slate-200"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};

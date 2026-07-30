import React from 'react';
import { Eye, ShieldAlert } from 'lucide-react';
import type { AuditEvent } from '../types';

interface AuditTableProps {
  events: AuditEvent[];
  onSelectEvent: (event: AuditEvent) => void;
}

export const AuditTable: React.FC<AuditTableProps> = ({ events, onSelectEvent }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
      <div className="p-4 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-full bg-slate-900 border-2 border-slate-800 text-white flex items-center justify-center shadow-xs">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">Recent Security Audit Events</h3>
            <p className="text-[11px] text-slate-500">Live telemetry stream of audited tool requests</p>
          </div>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider bg-slate-50">
              <th className="py-3 px-4">Request ID</th>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Tool</th>
              <th className="py-3 px-4">Decision</th>
              <th className="py-3 px-4">Risk Score</th>
              <th className="py-3 px-4">Matched Rules</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-xs">
            {events.map((event) => {
              const isBlocked = event.policy_result === 'BLOCK';
              return (
                <tr
                  key={event.request_id}
                  onClick={() => onSelectEvent(event)}
                  className="hover:bg-slate-50 transition cursor-pointer"
                >
                  <td className="py-3.5 px-4 font-mono text-slate-700">{event.request_id}</td>
                  <td className="py-3.5 px-4 text-slate-500 text-[11px]">{event.timestamp}</td>
                  <td className="py-3.5 px-4 font-mono text-slate-900 font-bold">{event.tool_name}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        isBlocked
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-lime-100 text-lime-800 border border-lime-300'
                      }`}
                    >
                      {event.policy_result}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-bold">
                    <span
                      className={
                        event.risk_score >= 0.7
                          ? 'text-rose-600'
                          : event.risk_score >= 0.4
                          ? 'text-amber-600'
                          : 'text-lime-600'
                      }
                    >
                      {(event.risk_score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-600">
                    {event.matched_rules.length > 0 ? (
                      <span className="text-rose-700 font-semibold">{event.matched_rules.join(', ')}</span>
                    ) : (
                      <span className="text-slate-400 italic">None</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectEvent(event);
                      }}
                      className="p-1 px-2.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition inline-flex items-center gap-1 text-[11px] border border-slate-200"
                    >
                      <Eye className="w-3.5 h-3.5 text-slate-700" /> Inspect
                    </button>
                  </td>
                </tr>
              );
            })}
            {events.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-400 text-xs italic">
                  No recent audit events recorded.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

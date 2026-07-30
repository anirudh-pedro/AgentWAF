import React, { useState } from 'react';
import { Search, Eye, ShieldAlert, ShieldCheck } from 'lucide-react';
import type { AuditEvent } from '../types';

interface AuditTableProps {
  events: AuditEvent[];
  onSelectEvent: (event: AuditEvent) => void;
}

export const AuditTable: React.FC<AuditTableProps> = ({ events, onSelectEvent }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [decisionFilter, setDecisionFilter] = useState<'ALL' | 'ALLOW' | 'BLOCK'>('ALL');

  const filteredEvents = events.filter((e) => {
    const matchesSearch =
      e.request_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.tool_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.matched_rules.some((r) => r.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesDecision = decisionFilter === 'ALL' || e.policy_result.toUpperCase() === decisionFilter;

    return matchesSearch && matchesDecision;
  });

  return (
    <div className="bg-[#1E293B] rounded-xl border border-[#334155] overflow-hidden shadow-sm">
      {/* Table Header & Controls Bar */}
      <div className="p-4 border-b border-[#334155] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-[#F8FAFC]">Security Audit Log Timeline</h3>
          <p className="text-xs text-[#94A3B8]">Live telemetry stream of inspected agent requests</p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          {/* Search Input */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-[#94A3B8] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search Request ID, Tool, Rule..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-[#0F172A] border border-[#334155] text-xs text-[#F8FAFC] placeholder-[#94A3B8] rounded-lg pl-9 pr-3 py-1.5 focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          {/* Decision Filter Pills */}
          <div className="flex items-center space-x-1 bg-[#0F172A] p-1 rounded-lg border border-[#334155]">
            {(['ALL', 'ALLOW', 'BLOCK'] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setDecisionFilter(filter)}
                className={`px-3 py-1 rounded-md text-[11px] font-semibold transition ${
                  decisionFilter === filter
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-[#94A3B8] hover:text-[#F8FAFC]'
                }`}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table Body */}
      <div className="overflow-x-auto max-h-[460px] overflow-y-auto">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-[#0F172A] border-b border-[#334155] text-[11px] font-semibold text-[#94A3B8] uppercase tracking-wider z-10">
            <tr>
              <th className="py-3 px-4">Request ID</th>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Tool</th>
              <th className="py-3 px-4">Decision</th>
              <th className="py-3 px-4">Risk Score</th>
              <th className="py-3 px-4">Matched Rules</th>
              <th className="py-3 px-4">Latency</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#334155] text-xs">
            {filteredEvents.map((event, idx) => {
              const isBlocked = event.policy_result === 'BLOCK';
              const rowBg = idx % 2 === 0 ? 'bg-[#1E293B]' : 'bg-[#0F172A]/50';

              return (
                <tr
                  key={event.request_id}
                  onClick={() => onSelectEvent(event)}
                  className={`${rowBg} hover:bg-slate-700/40 transition cursor-pointer`}
                >
                  <td className="py-3 px-4 font-mono text-[#F8FAFC] font-medium">{event.request_id}</td>
                  <td className="py-3 px-4 text-[#94A3B8] text-[11px]">{event.timestamp}</td>
                  <td className="py-3 px-4 font-mono text-[#F8FAFC] font-bold capitalize">{event.tool_name}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                        isBlocked
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                          : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      }`}
                    >
                      {isBlocked ? <ShieldAlert className="w-3 h-3" /> : <ShieldCheck className="w-3 h-3" />}
                      {event.policy_result}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-bold font-mono">
                    <span
                      className={
                        event.risk_score >= 0.7
                          ? 'text-rose-400'
                          : event.risk_score >= 0.4
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }
                    >
                      {(event.risk_score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-[#94A3B8]">
                    {event.matched_rules.length > 0 ? (
                      <span className="text-rose-400 font-semibold">{event.matched_rules.join(', ')}</span>
                    ) : (
                      <span className="text-slate-500 italic">None</span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-mono text-[#94A3B8]">{event.execution_time_ms.toFixed(2)} ms</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectEvent(event);
                      }}
                      className="p-1 px-2.5 rounded bg-[#0F172A] hover:bg-slate-700 text-[#F8FAFC] border border-[#334155] font-medium transition inline-flex items-center gap-1 text-[11px]"
                    >
                      <Eye className="w-3 h-3 text-blue-400" /> Inspect
                    </button>
                  </td>
                </tr>
              );
            })}
            {filteredEvents.length === 0 && (
              <tr>
                <td colSpan={8} className="py-10 text-center text-[#94A3B8] text-xs italic bg-[#0F172A]">
                  No audit log events found matching the filter criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

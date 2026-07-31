import React, { useState, useEffect } from 'react';
import { Search, Eye, ShieldAlert, ShieldCheck, EyeOff, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import type { AuditEvent } from '../types';

interface AuditTableProps {
  events: AuditEvent[];
  onSelectEvent: (event: AuditEvent) => void;
}

export const AuditTable: React.FC<AuditTableProps> = ({ events, onSelectEvent }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [decisionFilter, setDecisionFilter] = useState<'ALL' | 'ALLOW' | 'BLOCK' | 'SHADOW'>('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(8);

  const filteredEvents = events.filter((e) => {
    const matchesSearch =
      e.request_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.tool_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (e.matched_rules && e.matched_rules.some((r) => r.toLowerCase().includes(searchTerm.toLowerCase()))) ||
      (e.agent_scope && e.agent_scope.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (e.requested_resource && e.requested_resource.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesDecision =
      decisionFilter === 'ALL' ||
      (decisionFilter === 'SHADOW'
        ? e.policy_result.toUpperCase().includes('SHADOW')
        : e.policy_result.toUpperCase() === decisionFilter);

    return matchesSearch && matchesDecision;
  });

  // Reset to first page when search or filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, decisionFilter, pageSize]);

  const totalPages = Math.ceil(filteredEvents.length / pageSize) || 1;
  const safeCurrentPage = Math.min(Math.max(currentPage, 1), totalPages);
  const startIndex = (safeCurrentPage - 1) * pageSize;
  const paginatedEvents = filteredEvents.slice(startIndex, startIndex + pageSize);

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-2xs flex flex-col justify-between">
      <div>
        {/* Table Header Controls */}
        <div className="p-3 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-slate-50/50">
          <div>
            <h3 className="text-xs font-bold text-slate-800">Security Audit Log Timeline</h3>
            <p className="text-[10px] text-slate-400">Live telemetry stream of inspected requests</p>
          </div>

          <div className="flex items-center gap-2">
            {/* Search Input */}
            <div className="relative w-full sm:w-48">
              <Search className="w-3 h-3 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search ID, Tool, Resource, Rule..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-white border border-slate-200 text-[10px] text-slate-800 placeholder-slate-400 rounded pl-7 pr-2 py-1 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Decision Filter Pills */}
            <div className="flex items-center space-x-0.5 bg-slate-200/60 p-0.5 rounded border border-slate-200">
              {(['ALL', 'ALLOW', 'BLOCK', 'SHADOW'] as const).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setDecisionFilter(filter)}
                  className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase transition ${
                    decisionFilter === filter
                      ? 'bg-slate-900 text-white shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Table Body */}
        <div className="overflow-x-auto min-h-[280px]">
          <table className="w-full text-left border-collapse text-[11px]">
            <thead className="bg-slate-100 border-b border-slate-200 text-[9px] font-bold text-slate-500 uppercase tracking-wider z-10">
              <tr>
                <th className="py-2 px-3">Request ID</th>
                <th className="py-2 px-3">Timestamp</th>
                <th className="py-2 px-3">Tool</th>
                <th className="py-2 px-3">Scope / Resource</th>
                <th className="py-2 px-3">Decision</th>
                <th className="py-2 px-3">Risk Score</th>
                <th className="py-2 px-3">Matched Rules</th>
                <th className="py-2 px-3">Latency</th>
                <th className="py-2 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {paginatedEvents.map((event, idx) => {
                const res = event.policy_result.toUpperCase();
                const isBlocked = res === 'BLOCK';
                const isShadow = res === 'SHADOW_BLOCK' || res.includes('SHADOW');
                const rowBg = idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/40';

                return (
                  <tr
                    key={event.request_id}
                    onClick={() => onSelectEvent(event)}
                    className={`${rowBg} hover:bg-slate-100/60 transition cursor-pointer`}
                  >
                    <td className="py-2 px-3 font-mono text-slate-800 font-medium">{event.request_id}</td>
                    <td className="py-2 px-3 text-slate-400 text-[10px]">{event.timestamp}</td>
                    <td className="py-2 px-3 font-mono text-slate-800 font-bold capitalize">{event.tool_name}</td>
                    <td className="py-2 px-3 font-mono text-[10px]">
                      {event.requested_resource ? (
                        <span className="text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded border border-purple-200 font-medium">
                          {event.requested_resource}
                        </span>
                      ) : event.agent_scope ? (
                        <span className="text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                          {event.agent_scope}
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">-</span>
                      )}
                    </td>
                    <td className="py-2 px-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold border ${
                          isShadow
                            ? 'bg-purple-100 text-purple-800 border-purple-300'
                            : isBlocked
                            ? 'bg-rose-100 text-rose-700 border-rose-200'
                            : 'bg-emerald-100 text-emerald-700 border-emerald-200'
                        }`}
                      >
                        {isShadow ? (
                          <EyeOff className="w-2.5 h-2.5 text-purple-700" />
                        ) : isBlocked ? (
                          <ShieldAlert className="w-2.5 h-2.5" />
                        ) : (
                          <ShieldCheck className="w-2.5 h-2.5" />
                        )}
                        {event.policy_result}
                      </span>
                    </td>
                    <td className="py-2 px-3 font-bold font-mono">
                      <span
                        className={
                          event.risk_score >= 0.7
                            ? 'text-rose-600'
                            : event.risk_score >= 0.4
                            ? 'text-amber-600'
                            : 'text-emerald-600'
                        }
                      >
                        {(event.risk_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="py-2 px-3 font-mono text-slate-500 text-[10px]">
                      {event.matched_rules && event.matched_rules.length > 0 ? (
                        <span className="text-rose-600 font-semibold">{event.matched_rules.join(', ')}</span>
                      ) : (
                        <span className="text-slate-400 italic">None</span>
                      )}
                    </td>
                    <td className="py-2 px-3 font-mono text-slate-500 text-[10px]">{event.execution_time_ms.toFixed(2)} ms</td>
                    <td className="py-2 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectEvent(event);
                        }}
                        className="p-1 px-2 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 font-medium transition inline-flex items-center gap-1 text-[10px]"
                      >
                        <Eye className="w-3 h-3 text-blue-600" /> Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
              {filteredEvents.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400 text-[10px] italic bg-white">
                    No audit log events found matching the filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination Footer */}
      <div className="px-3 py-2 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] text-slate-600">
        <div className="flex items-center space-x-3">
          <span>
            Showing <strong className="text-slate-800">{filteredEvents.length > 0 ? startIndex + 1 : 0}</strong> to{' '}
            <strong className="text-slate-800">{Math.min(startIndex + pageSize, filteredEvents.length)}</strong> of{' '}
            <strong className="text-slate-800">{filteredEvents.length}</strong> events
          </span>

          <div className="flex items-center space-x-1 border-l border-slate-200 pl-3">
            <span className="text-slate-500">Rows:</span>
            <select
              value={pageSize}
              onChange={(e) => setPageSize(Number(e.target.value))}
              className="bg-white border border-slate-200 text-slate-800 rounded px-1.5 py-0.5 text-[10px] font-semibold focus:outline-none focus:border-blue-500"
            >
              <option value={5}>5</option>
              <option value={8}>8</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
            </select>
          </div>
        </div>

        {/* Page Navigation Controls */}
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setCurrentPage(1)}
            disabled={safeCurrentPage === 1}
            title="First Page"
            className="p-1 rounded bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <ChevronsLeft className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
            disabled={safeCurrentPage === 1}
            title="Previous Page"
            className="p-1 rounded bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>

          <span className="px-2 font-semibold text-slate-800">
            Page {safeCurrentPage} of {totalPages}
          </span>

          <button
            onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
            disabled={safeCurrentPage === totalPages}
            title="Next Page"
            className="p-1 rounded bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setCurrentPage(totalPages)}
            disabled={safeCurrentPage === totalPages}
            title="Last Page"
            className="p-1 rounded bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <ChevronsRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};

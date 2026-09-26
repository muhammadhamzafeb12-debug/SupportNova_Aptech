import React, { useState, useEffect } from 'react';
import { Search, Filter, Plus, ArrowRight } from 'lucide-react';

export const ComplaintsListPage = ({ onSelectComplaint, onNavigate }) => {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetchComplaints();
  }, [search, statusFilter]);

  const fetchComplaints = async () => {
    try {
      setLoading(true);
      let url = `/api/complaints?search=${encodeURIComponent(search)}`;
      if (statusFilter) url += `&status_filter=${encodeURIComponent(statusFilter)}`;
      const res = await fetch(url);
      if (res.ok) setComplaints(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
            Case Management Queue
          </h1>
          <p className="text-xs lg:text-sm text-slate-400 mt-1">
            Enterprise customer complaint records, priority triage, and verification status.
          </p>
        </div>
        <button
          onClick={() => onNavigate('submit')}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-all flex items-center gap-2 shrink-0 shadow-lg shadow-blue-500/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Complaint</span>
        </button>
      </div>

      {/* Toolbar & Filters */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 flex flex-wrap gap-3 items-center justify-between shadow-xl">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by Complaint ID, title, or category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="NEW">Open</option>
            <option value="ANALYZED">Under Review</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="ESCALATED">Escalated</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 font-medium">Loading complaint records...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-slate-900 text-slate-400 text-[11px] uppercase font-bold border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Ticket ID</th>
                  <th className="p-3.5">Title</th>
                  <th className="p-3.5">Customer Type</th>
                  <th className="p-3.5">Department</th>
                  <th className="p-3.5">Priority</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Verification</th>
                  <th className="p-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {complaints.map((c) => {
                  const isMatch = c.comparison_status === 'MATCH';
                  const isMismatch = c.comparison_status === 'REVIEW REQUIRED' || c.comparison_status === 'MISMATCH';

                  return (
                    <tr key={c.id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="p-3.5 font-mono font-bold text-blue-400">{c.complaint_code}</td>
                      <td className="p-3.5 font-semibold text-white max-w-xs truncate">{c.title}</td>
                      <td className="p-3.5 text-slate-300">{c.customer_type || 'Regular'}</td>
                      <td className="p-3.5 text-slate-300">{c.department || 'Customer Relations'}</td>
                      <td className="p-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            c.priority?.includes('P0')
                              ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                              : c.priority?.includes('P1')
                              ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                              : 'bg-slate-800 text-slate-300 border-slate-700'
                          }`}
                        >
                          {c.priority || 'P2 – Medium'}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-900 text-slate-200 border border-slate-800">
                          {c.status}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            isMatch
                              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                              : isMismatch
                              ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                              : 'bg-slate-800 text-slate-400 border-slate-700'
                          }`}
                        >
                          {c.comparison_status || 'PENDING'}
                        </span>
                      </td>
                      <td className="p-3.5 text-right">
                        <button
                          onClick={() => onSelectComplaint(c.id)}
                          className="px-2.5 py-1 text-xs font-bold text-blue-400 hover:text-white bg-blue-500/10 hover:bg-blue-600 rounded border border-blue-500/20 transition-all"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

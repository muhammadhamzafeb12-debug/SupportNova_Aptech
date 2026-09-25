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
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#202838]">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
            Case Management
          </h1>
          <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
            Enterprise customer complaint queue and decision status
          </p>
        </div>
        <button
          onClick={() => onNavigate('submit')}
          className="px-4 py-2 bg-[#635BFF] hover:bg-[#5249E6] text-white text-xs font-semibold rounded-md transition-colors flex items-center gap-2 shrink-0 shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>New Complaint</span>
        </button>
      </div>

      {/* Toolbar & Filters */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 flex flex-wrap gap-3 items-center justify-between">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-3.5 h-3.5 text-[#98A2B3] absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by Complaint ID, title, or category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#151B28] border border-[#202838] rounded-md pl-9 pr-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-[#98A2B3]" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#151B28] border border-[#202838] rounded-md px-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
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
      <div className="bg-[#101521] border border-[#202838] rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#98A2B3]">Loading complaint records...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-[#F4F6FA]">
              <thead className="bg-[#151B28] text-[#98A2B3] text-[11px] uppercase font-semibold border-b border-[#202838]">
                <tr>
                  <th className="p-3">Complaint ID</th>
                  <th className="p-3">Title</th>
                  <th className="p-3">Customer</th>
                  <th className="p-3">Department</th>
                  <th className="p-3">Priority</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Verification</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202838]">
                {complaints.map((c) => {
                  const isMatch = c.comparison_status === 'MATCH';
                  const isMismatch = c.comparison_status === 'REVIEW REQUIRED' || c.comparison_status === 'MISMATCH';

                  return (
                    <tr key={c.id} className="hover:bg-[#151B28]/50 transition-colors">
                      <td className="p-3 font-mono font-medium text-[#635BFF]">{c.complaint_code}</td>
                      <td className="p-3 font-medium text-[#F4F6FA] max-w-xs truncate">{c.title}</td>
                      <td className="p-3 text-[#98A2B3]">{c.customer_type || 'Regular'}</td>
                      <td className="p-3 text-[#F4F6FA]">{c.department || 'Customer Relations'}</td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            c.priority?.includes('P0')
                              ? 'bg-red-500/10 text-red-400 border-red-500/20'
                              : c.priority?.includes('P1')
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                              : 'bg-[#151B28] text-[#98A2B3] border-[#202838]'
                          }`}
                        >
                          {c.priority || 'P2 – Medium'}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-[#151B28] text-[#F4F6FA] border border-[#202838]">
                          {c.status}
                        </span>
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            isMatch
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : isMismatch
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                              : 'bg-[#151B28] text-[#98A2B3] border-[#202838]'
                          }`}
                        >
                          {c.comparison_status || 'PENDING'}
                        </span>
                      </td>
                      <td className="p-3 text-right">
                        <button
                          onClick={() => onSelectComplaint(c.id)}
                          className="px-2.5 py-1 text-xs font-medium text-[#635BFF] hover:bg-[#151B28] rounded border border-[#202838] transition-colors"
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

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  FileText, ShieldCheck, AlertTriangle, CheckCircle2, TrendingUp,
  ArrowRight, ShieldAlert, Clock, Plus, Search, Filter, Cpu, CheckCircle
} from 'lucide-react';

export const DashboardPage = ({ onSelectComplaint, onNavigate }) => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentComplaints, setRecentComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [resStats, resComp] = await Promise.all([
        fetch('/api/analytics/summary'),
        fetch('/api/complaints?limit=10')
      ]);
      if (resStats.ok) setStats(await resStats.json());
      if (resComp.ok) setRecentComplaints(await resComp.json());
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredComplaints = recentComplaints.filter((c) => {
    const matchesSearch =
      c.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.complaint_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.category?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#635BFF]"></div>
      </div>
    );
  }

  const openCount = stats?.overview?.total_complaints - (stats?.overview?.resolved || 0) || 0;
  const underReviewCount = (stats?.overview?.escalated || 0) + (stats?.comparison_breakdown?.reviews_required || 0);
  const resolvedTodayCount = stats?.overview?.resolved || 0;
  const criticalCount = stats?.priority_breakdown?.P0_Critical || 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#202838]">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
            Operations Dashboard
          </h1>
          <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
            Complaint resolution and verification overview
          </p>
        </div>
        <button
          onClick={() => onNavigate('submit')}
          className="px-4 py-2 bg-[#635BFF] hover:bg-[#5249E6] text-white text-xs font-semibold rounded-md transition-colors flex items-center gap-2 shrink-0 shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Submit New Complaint</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-[#98A2B3]">
            <span className="text-xs font-medium">Open Complaints</span>
            <FileText className="w-4 h-4 text-[#635BFF]" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#F4F6FA]">{openCount}</span>
            <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-medium">
              <TrendingUp className="w-3 h-3" /> +4.2%
            </span>
          </div>
          <p className="text-[11px] text-[#98A2B3]">Active complaints requiring triage</p>
        </div>

        {/* KPI 2 */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-[#98A2B3]">
            <span className="text-xs font-medium">Under Review</span>
            <AlertTriangle className="w-4 h-4 text-[#F59E0B]" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#F59E0B]">{underReviewCount}</span>
            <span className="text-[11px] text-[#98A2B3]">Pending Sign-off</span>
          </div>
          <p className="text-[11px] text-[#98A2B3]">Cases flagged for manual review</p>
        </div>

        {/* KPI 3 */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-[#98A2B3]">
            <span className="text-xs font-medium">Resolved Today</span>
            <CheckCircle2 className="w-4 h-4 text-[#22C55E]" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#22C55E]">{resolvedTodayCount}</span>
            <span className="text-[11px] text-emerald-400 font-medium">98.4% SLA</span>
          </div>
          <p className="text-[11px] text-[#98A2B3]">Verified and closed cases</p>
        </div>

        {/* KPI 4 */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-[#98A2B3]">
            <span className="text-xs font-medium">Critical Cases (P0)</span>
            <ShieldAlert className="w-4 h-4 text-[#EF4444]" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold text-[#EF4444]">{criticalCount}</span>
            <span className="text-[11px] text-[#EF4444] font-medium">High Priority</span>
          </div>
          <p className="text-[11px] text-[#98A2B3]">Safety & emergency hazard cases</p>
        </div>
      </div>

      {/* DUAL-PIPELINE: Decision Verification Workflow */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-[#202838] pb-3">
          <div>
            <h2 className="text-base font-semibold text-[#F4F6FA]">Decision Verification</h2>
            <p className="text-xs text-[#98A2B3]">Dual-pipeline resolution workflow</p>
          </div>
          <span className="text-xs font-mono text-[#635BFF] bg-[#151B28] px-2.5 py-1 rounded border border-[#202838]">
            AI vs Ground-Truth Engine
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
          {/* Step 1 */}
          <div className="bg-[#151B28] border border-[#202838] rounded-md p-3 text-center space-y-1">
            <div className="text-[10px] font-semibold text-[#98A2B3] uppercase">Stage 1</div>
            <div className="text-xs font-semibold text-[#F4F6FA]">Complaint Received</div>
            <p className="text-[11px] text-[#98A2B3]">Sanitization & Input Defense</p>
          </div>

          {/* Step 2 */}
          <div className="bg-[#151B28] border border-[#202838] rounded-md p-3 text-center space-y-1">
            <div className="text-[10px] font-semibold text-[#635BFF] uppercase">Pipeline 1</div>
            <div className="text-xs font-semibold text-[#F4F6FA]">AI Analysis</div>
            <p className="text-[11px] text-[#98A2B3]">Google Gemini API / Structured JSON</p>
          </div>

          {/* Step 3 */}
          <div className="bg-[#151B28] border border-[#202838] rounded-md p-3 text-center space-y-1">
            <div className="text-[10px] font-semibold text-emerald-400 uppercase">Pipeline 2</div>
            <div className="text-xs font-semibold text-[#F4F6FA]">Independent Rule Validation</div>
            <p className="text-[11px] text-[#98A2B3]">100+ Rule Matrix Engine</p>
          </div>

          {/* Step 4 */}
          <div className="bg-[#151B28] border border-[#202838] rounded-md p-3 text-center space-y-1">
            <div className="text-[10px] font-semibold text-amber-400 uppercase">Stage 4</div>
            <div className="text-xs font-semibold text-[#F4F6FA]">Verification</div>
            <p className="text-[11px] text-[#98A2B3]">7 Empirical Compliance Metrics</p>
          </div>

          {/* Step 5 */}
          <div className="bg-[#151B28] border border-[#202838] rounded-md p-3 text-center space-y-1">
            <div className="text-[10px] font-semibold text-purple-400 uppercase">Final Output</div>
            <div className="text-xs font-semibold text-[#F4F6FA]">Final Decision</div>
            <p className="text-[11px] text-[#98A2B3]">Auto Approve / Manual Review</p>
          </div>
        </div>
      </div>

      {/* RECENT COMPLAINTS TABLE */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
        {/* Table Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#202838] pb-3">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-[#F4F6FA]">Recent Complaints</h2>
            <span className="text-xs text-[#98A2B3]">({filteredComplaints.length} tickets)</span>
          </div>

          <div className="flex items-center gap-2">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-[#98A2B3] absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search complaints..."
                className="bg-[#151B28] border border-[#202838] rounded-md pl-8 pr-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF] w-48"
              />
            </div>

            {/* Filter Dropdown */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-[#151B28] border border-[#202838] rounded-md px-2.5 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
            >
              <option value="ALL">All Statuses</option>
              <option value="NEW">Open</option>
              <option value="ANALYZED">Under Review</option>
              <option value="ESCALATED">Escalated</option>
              <option value="RESOLVED">Resolved</option>
            </select>

            <button
              onClick={() => onNavigate('complaints')}
              className="text-xs text-[#635BFF] hover:underline font-medium flex items-center gap-1 pl-2"
            >
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Enterprise Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-[#F4F6FA]">
            <thead className="bg-[#151B28] text-[#98A2B3] text-[11px] uppercase font-semibold border-b border-[#202838]">
              <tr>
                <th className="p-3">Complaint ID</th>
                <th className="p-3">Customer</th>
                <th className="p-3">Category</th>
                <th className="p-3">Priority</th>
                <th className="p-3">Status</th>
                <th className="p-3">Verification</th>
                <th className="p-3">Last Updated</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#202838]">
              {filteredComplaints.map((c) => {
                const isMatch = c.comparison_status === 'MATCH';
                const isMismatch = c.comparison_status === 'REVIEW REQUIRED' || c.comparison_status === 'MISMATCH';

                return (
                  <tr key={c.id} className="hover:bg-[#151B28]/50 transition-colors">
                    <td className="p-3 font-mono font-medium text-[#635BFF]">{c.complaint_code}</td>
                    <td className="p-3 font-medium text-[#F4F6FA]">{c.customer_type || 'Regular Customer'}</td>
                    <td className="p-3 text-[#98A2B3]">{c.category || 'Service Quality'}</td>
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
                    <td className="p-3 text-[#98A2B3]">
                      {c.submitted_at ? new Date(c.submitted_at).toLocaleDateString() : 'Today'}
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
      </div>
    </div>
  );
};

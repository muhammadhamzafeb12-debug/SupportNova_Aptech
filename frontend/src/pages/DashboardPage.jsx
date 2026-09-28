import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  FileText, ShieldCheck, AlertTriangle, CheckCircle2,
  ArrowRight, ShieldAlert, Clock, Plus, Search, Cpu, BarChart3, Activity, Layers, Scale, Sparkles, Users
} from 'lucide-react';

export const DashboardPage = ({ onSelectComplaint, onNavigate }) => {
  const { user, token, switchRoleDemo } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentComplaints, setRecentComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  useEffect(() => {
    fetchDashboardData();
  }, [token]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const [resStats, resComp] = await Promise.all([
        fetch('/api/analytics/summary', { headers }),
        fetch('/api/complaints?limit=10', { headers })
      ]);
      if (resStats.ok) setStats(await resStats.json());
      if (resComp.ok) setRecentComplaints(await resComp.json());
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const role = user?.role || 'CUSTOMER';

  const getHeaderInfo = () => {
    switch (role) {
      case 'ADMIN':
        return {
          title: 'System Administration & Global Operations',
          badge: 'All Roles & System Scope',
          subtitle: 'System-wide complaint telemetry, cross-department analytics, and full operational authority.'
        };
      case 'MANAGER':
        return {
          title: 'Department Operations Dashboard',
          badge: 'Department Scope',
          subtitle: 'Viewing tickets, SLA compliance, and verification performance for your assigned department.'
        };
      case 'AGENT':
        return {
          title: 'Support Agent Workstation',
          badge: 'Agent Assigned Queue',
          subtitle: 'Manage your assigned complaints, priority triage, and resolution tasks.'
        };
      case 'REVIEWER':
        return {
          title: 'Compliance & Review Overview',
          badge: 'Reviewer Scope',
          subtitle: 'Monitor complaint volumes and verification scores. Go to Reviewer Dashboard to review and route complaints.'
        };
      case 'CUSTOMER':
      default:
        return {
          title: 'Customer Service Dashboard',
          badge: 'Personal Account Only',
          subtitle: 'Track your submitted support complaints, resolution status, and active tickets.'
        };
    }
  };

  const headerInfo = getHeaderInfo();

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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const totalComplaints = stats?.overview?.total_complaints ?? 0;
  const resolvedCount = stats?.overview?.resolved ?? 0;
  const escalatedCount = stats?.overview?.escalated ?? 0;
  const analyzedCount = stats?.overview?.analyzed ?? 0;
  const pendingCount = totalComplaints - resolvedCount - escalatedCount - analyzedCount;
  const underReviewCount = escalatedCount + (stats?.comparison_breakdown?.reviews_required ?? 0);
  const agreementRate = stats?.overview?.agreement_rate ?? 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            {headerInfo.title}
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              {headerInfo.badge}
            </span>
          </h1>
          <p className="text-xs lg:text-sm text-slate-400 mt-1">
            {headerInfo.subtitle}
          </p>
        </div>
        {role !== 'ADMIN' && role !== 'REVIEWER' && (
          <button
            onClick={() => onNavigate('submit')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-all flex items-center gap-2 shrink-0 shadow-lg shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Submit New Complaint</span>
          </button>
        )}
      </div>

      {/* QUICK ROLE DASHBOARD SWITCHER BAR — for ADMIN role */}
      {role === 'ADMIN' && (
        <div className="bg-[#0D1322] border border-purple-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xl bg-gradient-to-r from-purple-950/20 via-slate-900 to-slate-900">
          <div className="flex items-center gap-2.5 text-xs font-bold text-white">
            <Users className="w-4.5 h-4.5 text-purple-400 shrink-0" />
            <span>Open Role Dashboard:</span>
            <span className="text-[11px] font-normal text-slate-400 hidden lg:inline">(Inspect any role's operational view with 1 click)</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {[
              { id: 'CUSTOMER', label: 'Customer View', color: 'hover:bg-emerald-500/20 hover:text-emerald-300 border-emerald-500/30' },
              { id: 'AGENT', label: 'Agent View', color: 'hover:bg-cyan-500/20 hover:text-cyan-300 border-cyan-500/30' },
              { id: 'REVIEWER', label: 'Reviewer View', color: 'hover:bg-amber-500/20 hover:text-amber-300 border-amber-500/30' },
              { id: 'MANAGER', label: 'Manager View', color: 'hover:bg-blue-500/20 hover:text-blue-300 border-blue-500/30' },
              { id: 'ADMIN', label: 'Admin View', color: 'bg-purple-600/40 text-purple-300 border-purple-500/50 font-extrabold' },
            ].map((r) => (
              <button
                key={r.id}
                onClick={async () => {
                  try {
                    await switchRoleDemo(r.id);
                  } catch (err) {
                    console.error('Failed to switch role view:', err);
                  }
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all ${
                  r.id === 'ADMIN'
                    ? r.color
                    : 'bg-slate-900/90 text-slate-300 border-slate-800 ' + r.color
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* REVIEWER — Quick Access Banner */}
      {role === 'REVIEWER' && (
        <div className="bg-gradient-to-r from-amber-950/30 via-[#0D1322] to-[#0D1322] border border-amber-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-sm font-bold text-white">Reviewer Dashboard Ready</p>
              <p className="text-xs text-slate-400">View complaints, use the AI assistant, and route cases to department managers.</p>
            </div>
          </div>
          <button
            onClick={() => onNavigate('reviews')}
            className="px-4 py-2.5 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white text-xs font-bold rounded-lg transition-all flex items-center gap-2 shrink-0 shadow-lg shadow-amber-500/20 whitespace-nowrap"
          >
            <ArrowRight className="w-4 h-4" />
            Open Reviewer Dashboard
          </button>
        </div>
      )}

      {/* CUSTOMER PERSONAL METRIC CARDS */}
      {role === 'CUSTOMER' && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="glass-card rounded-xl p-5 space-y-3 relative overflow-hidden group">
            <div className="flex items-center justify-between text-slate-300 gap-1">
              <span className="text-[11px] font-bold uppercase tracking-wider truncate">My Total Complaints</span>
              <FileText className="w-4 h-4 text-blue-400 shrink-0" />
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-2xl font-extrabold text-white tracking-tight">{recentComplaints.length}</span>
              <span className="text-[10px] font-semibold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 shrink-0">
                Submitted
              </span>
            </div>
            <p className="text-[10px] text-slate-400 truncate">Total complaints created by you</p>
          </div>

          <div className="glass-card rounded-xl p-5 space-y-3 relative overflow-hidden group">
            <div className="flex items-center justify-between text-slate-300 gap-1">
              <span className="text-[11px] font-bold uppercase tracking-wider truncate">Active / In Progress</span>
              <Clock className="w-4 h-4 text-cyan-400 shrink-0" />
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-2xl font-extrabold text-cyan-400 tracking-tight">
                {recentComplaints.filter(c => c.status !== 'RESOLVED' && c.status !== 'CLOSED').length}
              </span>
              <span className="text-[10px] font-semibold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20 shrink-0">
                Open
              </span>
            </div>
            <p className="text-[10px] text-slate-400 truncate">Awaiting resolution or under review</p>
          </div>

          <div className="glass-card rounded-xl p-5 space-y-3 relative overflow-hidden group">
            <div className="flex items-center justify-between text-slate-300 gap-1">
              <span className="text-[11px] font-bold uppercase tracking-wider truncate">Resolved</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-2xl font-extrabold text-emerald-400 tracking-tight">
                {recentComplaints.filter(c => c.status === 'RESOLVED' || c.status === 'CLOSED').length}
              </span>
              <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 shrink-0">
                Completed
              </span>
            </div>
            <p className="text-[10px] text-slate-400 truncate">Successfully closed tickets</p>
          </div>
        </div>
      )}

      {/* Overview Metric Cards Grid — for AGENT, REVIEWER, MANAGER, ADMIN */}
      {role !== 'CUSTOMER' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Metric 1: Total Complaints */}
          <div className="glass-card rounded-xl p-5 space-y-3 relative overflow-hidden group">
            <div className="flex items-center justify-between text-slate-300 gap-1">
              <span className="text-[11px] font-bold uppercase tracking-wider truncate">Total Complaints</span>
              <FileText className="w-4 h-4 text-blue-400 shrink-0" />
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-2xl font-extrabold text-white tracking-tight">{totalComplaints}</span>
              {totalComplaints > 0 && (
                <span className="text-[10px] font-semibold text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700 shrink-0">
                  DB Records
                </span>
              )}
            </div>
            <p className="text-[10px] text-slate-400 truncate">Logged across all channels</p>
          </div>

          {/* Metric 2: Pending */}
          <div className="glass-card rounded-xl p-5 space-y-3 relative overflow-hidden group">
            <div className="flex items-center justify-between text-slate-300 gap-1">
              <span className="text-[11px] font-bold uppercase tracking-wider truncate">Pending Action</span>
              <Clock className="w-4 h-4 text-cyan-400 shrink-0" />
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-2xl font-extrabold text-cyan-400 tracking-tight">{pendingCount}</span>
              <span className="text-[10px] font-semibold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20 shrink-0">
                Active Queue
              </span>
            </div>
            <p className="text-[10px] text-slate-400 truncate">Requiring agent resolution</p>
          </div>

          {/* Metric 3: Under Review */}
          <div className="glass-card rounded-xl p-5 space-y-3 relative overflow-hidden group">
            <div className="flex items-center justify-between text-slate-300 gap-1">
              <span className="text-[11px] font-bold uppercase tracking-wider truncate">Under Review</span>
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-2xl font-extrabold text-amber-400 tracking-tight">{underReviewCount}</span>
              <span className="text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 shrink-0">
                Flagged
              </span>
            </div>
            <p className="text-[10px] text-slate-400 truncate">Score mismatch override</p>
          </div>

          {/* Metric 4: Resolved */}
          <div className="glass-card rounded-xl p-5 space-y-3 relative overflow-hidden group">
            <div className="flex items-center justify-between text-slate-300 gap-1">
              <span className="text-[11px] font-bold uppercase tracking-wider truncate">Resolved</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-2xl font-extrabold text-emerald-400 tracking-tight">{resolvedCount}</span>
              <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 shrink-0">
                {totalComplaints > 0 ? Math.round((resolvedCount / totalComplaints) * 100) : 0}% Closed
              </span>
            </div>
            <p className="text-[10px] text-slate-400 truncate">Verified and closed</p>
          </div>

          {/* Metric 5: Verification Agreement */}
          <div className="glass-card rounded-xl p-5 space-y-3 relative overflow-hidden group">
            <div className="flex items-center justify-between text-slate-300 gap-1">
              <span className="text-[11px] font-bold uppercase tracking-wider truncate">Verification Score</span>
              <Scale className="w-4 h-4 text-indigo-400 shrink-0" />
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-2xl font-extrabold text-indigo-400 tracking-tight">{agreementRate}%</span>
              <span className="text-[10px] font-semibold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20 shrink-0">
                Match Rate
              </span>
            </div>
            <p className="text-[10px] text-slate-400 truncate">AI vs Python Compliance</p>
          </div>
        </div>
      )}

      {/* DUAL-PIPELINE ARCHITECTURE PANEL — hidden for AGENT and CUSTOMER roles */}
      {role !== 'AGENT' && role !== 'CUSTOMER' && (
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Cpu className="w-5 h-5 text-blue-400" /> Dual-Pipeline Verification Architecture
              </h2>
              <p className="text-xs text-slate-400">Generative AI Reasoning + Independent Ground-Truth Python Rule Engine</p>
            </div>
            <span className="text-xs font-mono font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20 self-start sm:self-auto">
              Ground-Truth Verified
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 text-center space-y-1 hover:border-blue-500/40 transition-all">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Step 1</div>
              <div className="text-xs font-bold text-white">Input Defense</div>
              <p className="text-[11px] text-slate-400">Sanitization & Anti-Injection</p>
            </div>

            <div className="bg-slate-900/90 border border-blue-500/30 rounded-xl p-3.5 text-center space-y-1 hover:border-blue-400 transition-all bg-gradient-to-b from-blue-500/10 to-transparent">
              <div className="text-[10px] font-bold text-blue-400 uppercase tracking-wider">Pipeline 1</div>
              <div className="text-xs font-bold text-white">GenAI Engine</div>
              <p className="text-[11px] text-slate-400">LLM Sentiment & Categorization</p>
            </div>

            <div className="bg-slate-900/90 border border-cyan-500/30 rounded-xl p-3.5 text-center space-y-1 hover:border-cyan-400 transition-all bg-gradient-to-b from-cyan-500/10 to-transparent">
              <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Pipeline 2</div>
              <div className="text-xs font-bold text-white">Python Validation</div>
              <p className="text-[11px] text-slate-400">100+ Rule Ground-Truth</p>
            </div>

            <div className="bg-slate-900/90 border border-amber-500/30 rounded-xl p-3.5 text-center space-y-1 hover:border-amber-400 transition-all bg-gradient-to-b from-amber-500/10 to-transparent">
              <div className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">Comparator</div>
              <div className="text-xs font-bold text-white">7 Score Cards</div>
              <p className="text-[11px] text-slate-400">Policy & Routing Compliance</p>
            </div>

            <div className="bg-slate-900/90 border border-emerald-500/30 rounded-xl p-3.5 text-center space-y-1 hover:border-emerald-400 transition-all bg-gradient-to-b from-emerald-500/10 to-transparent">
              <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">Output</div>
              <div className="text-xs font-bold text-white">Final Decision</div>
              <p className="text-[11px] text-slate-400">Auto-Approve or Review Queue</p>
            </div>
          </div>
        </div>
      )}

      {/* CUSTOMER'S OWN COMPLAINTS TABLE */}
      {role === 'CUSTOMER' && (
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white">My Complaints</h2>
              <span className="text-xs text-slate-400">({filteredComplaints.length} tickets)</span>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search my tickets..."
                  className="bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500 w-44 sm:w-56"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="NEW">New</option>
                <option value="ANALYZED">Analyzed</option>
                <option value="ESCALATED">Escalated</option>
                <option value="RESOLVED">Resolved</option>
              </select>
            </div>
          </div>

          {filteredComplaints.length === 0 ? (
            <div className="py-10 text-center space-y-3">
              <p className="text-sm text-slate-400">You have no active complaints matching your search.</p>
              <button
                onClick={() => onNavigate('submit')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-all inline-flex items-center gap-2 shadow-lg shadow-blue-500/20"
              >
                <Plus className="w-4 h-4" />
                <span>Submit New Complaint</span>
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-200">
                <thead className="bg-slate-900 text-slate-400 text-[11px] uppercase font-bold border-b border-slate-800">
                  <tr>
                    <th className="p-3">Ticket ID</th>
                    <th className="p-3">Title</th>
                    <th className="p-3">Category</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredComplaints.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="p-3 font-mono font-bold text-blue-400">{c.complaint_code}</td>
                      <td className="p-3 font-medium text-white max-w-xs truncate">{c.title}</td>
                      <td className="p-3 text-slate-300">{c.category || 'General Service'}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-900 text-slate-200 border border-slate-800">
                          {c.status}
                        </span>
                      </td>
                      <td className="p-3 text-right">
                        <button
                          onClick={() => onSelectComplaint(c.id)}
                          className="px-2.5 py-1 text-xs font-bold text-blue-400 hover:text-white bg-blue-500/10 hover:bg-blue-600 rounded border border-blue-500/20 transition-all"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* RECENT COMPLAINTS TABLE — hidden for CUSTOMER role */}
      {role !== 'CUSTOMER' && (
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white">Recent Complaints Queue</h2>
              <span className="text-xs text-slate-400">({filteredComplaints.length} loaded)</span>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search ticket, code..."
                  className="bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500 w-44 sm:w-56"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="NEW">New</option>
                <option value="ANALYZED">Analyzed</option>
                <option value="ESCALATED">Escalated</option>
                <option value="RESOLVED">Resolved</option>
              </select>

              <button
                onClick={() => onNavigate('complaints')}
                className="text-xs text-blue-400 hover:text-blue-300 font-bold flex items-center gap-1 pl-1"
              >
                <span>View all</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Responsive Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-slate-900 text-slate-400 text-[11px] uppercase font-bold border-b border-slate-800">
                <tr>
                  <th className="p-3">Ticket ID</th>
                  <th className="p-3">Customer</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Priority</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Verification</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredComplaints.map((c) => {
                  const isMatch = c.comparison_status === 'MATCH';
                  const isReview = c.comparison_status === 'REVIEW REQUIRED' || c.comparison_status === 'MISMATCH';

                  return (
                    <tr key={c.id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="p-3 font-mono font-bold text-blue-400">{c.complaint_code}</td>
                      <td className="p-3 font-medium text-white">{c.customer_type || 'Regular Customer'}</td>
                      <td className="p-3 text-slate-300">{c.category || 'Service Quality'}</td>
                      <td className="p-3">
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
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-900 text-slate-200 border border-slate-800">
                          {c.status}
                        </span>
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            isMatch
                              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                              : isReview
                              ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                              : 'bg-slate-800 text-slate-400 border-slate-700'
                          }`}
                        >
                          {c.comparison_status || 'PENDING'}
                        </span>
                      </td>
                      <td className="p-3 text-right">
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
        </div>
      )}
    </div>
  );
};

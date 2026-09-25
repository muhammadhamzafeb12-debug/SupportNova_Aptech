import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';
import { FileText, PlusCircle, CheckCircle, Clock, DollarSign } from 'lucide-react';
import { Link } from 'react-router-dom';

export const CustomerDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getDashboard('customer');
        setData(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="text-center py-12 text-slate-400 text-xs">Loading Customer Dashboard...</div>;
  }

  const metrics = data?.metrics || {};
  const complaints = data?.complaints || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Welcome, {data?.user_name || 'Valued Customer'}</h1>
          <p className="text-xs text-slate-400 mt-1">Track your active complaints, resolution progress, and credit adjustments.</p>
        </div>
        <Link
          to="/submit-complaint"
          className="bg-brand-600 hover:bg-brand-500 text-white font-semibold px-4 py-2 rounded-xl text-xs flex items-center space-x-2 transition shadow-lg shadow-brand-500/20"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Complaint</span>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Total Complaints" value={metrics.total_submitted || 0} icon={<FileText className="w-4 h-4" />} />
        <StatCard title="Pending Resolution" value={metrics.pending_resolution || 0} icon={<Clock className="w-4 h-4" />} />
        <StatCard title="Resolved Cases" value={metrics.resolved_complaints || 0} icon={<CheckCircle className="w-4 h-4" />} />
        <StatCard title="Approved Credits" value={`$${metrics.total_credits_approved || 0}`} icon={<DollarSign className="w-4 h-4" />} />
      </div>

      <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">My Complaint History</h2>
        {complaints.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">You have not submitted any complaints yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-3">Complaint #</th>
                  <th className="py-3 px-3">Title</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Priority</th>
                  <th className="py-3 px-3">Credit Issued</th>
                  <th className="py-3 px-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {complaints.map((c: any) => (
                  <tr key={c.id} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 px-3 font-mono text-brand-400 font-medium">{c.complaint_number}</td>
                    <td className="py-3 px-3 font-semibold text-white">{c.title}</td>
                    <td className="py-3 px-3 text-slate-300">{c.category}</td>
                    <td className="py-3 px-3"><StatusBadge status={c.status} type="status" /></td>
                    <td className="py-3 px-3"><StatusBadge status={c.priority} type="priority" /></td>
                    <td className="py-3 px-3 text-emerald-400 font-semibold">${c.approved_credit || 0}</td>
                    <td className="py-3 px-3 text-slate-400">{c.created_at?.split('T')[0]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

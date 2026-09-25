import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { StatCard } from '../components/StatCard';
import { LayoutDashboard, DollarSign, TrendingUp, ShieldAlert, BarChart2 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

export const ManagerDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getDashboard('manager');
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
    return <div className="text-center py-12 text-slate-400 text-xs">Loading Executive Manager Dashboard...</div>;
  }

  const metrics = data?.metrics || {};
  const byDept = data?.by_department || {};
  const auditLogs = data?.recent_activity || [];

  const deptData = Object.keys(byDept).map((dept) => ({
    name: dept,
    count: byDept[dept],
  }));

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Executive Manager Dashboard</h1>
        <p className="text-xs text-slate-400 mt-1">High-level operational metrics, SLA compliance, and department distribution.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Total Complaints" value={metrics.total_complaints || 0} icon={<LayoutDashboard className="w-4 h-4" />} />
        <StatCard title="Resolution Rate" value={`${metrics.resolution_rate || 0}%`} trend="+4.2%" icon={<TrendingUp className="w-4 h-4 text-emerald-400" />} />
        <StatCard title="Total Credits Issued" value={`$${metrics.total_financial_credits || 0}`} icon={<DollarSign className="w-4 h-4 text-emerald-400" />} />
        <StatCard title="SLA Compliance" value={`${metrics.sla_compliance_percent || 94.5}%`} icon={<BarChart2 className="w-4 h-4 text-brand-400" />} />
      </div>

      <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Volume by Department</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={deptData}>
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {deptData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Recent System Audit Trail</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Complaint #</th>
                <th className="py-2.5 px-3">Action</th>
                <th className="py-2.5 px-3">User</th>
                <th className="py-2.5 px-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {auditLogs.map((log: any, idx: number) => (
                <tr key={idx} className="hover:bg-slate-900/40 transition">
                  <td className="py-2.5 px-3 text-slate-500 font-mono">{log.timestamp?.replace('T', ' ')?.substring(0, 19)}</td>
                  <td className="py-2.5 px-3 font-mono text-brand-400 font-bold">{log.complaint_number}</td>
                  <td className="py-2.5 px-3 font-semibold text-white">{log.action}</td>
                  <td className="py-2.5 px-3 text-slate-300">{log.performed_by}</td>
                  <td className="py-2.5 px-3 text-slate-400">{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

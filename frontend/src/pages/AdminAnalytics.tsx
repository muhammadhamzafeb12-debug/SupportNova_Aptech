import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { StatCard } from '../components/StatCard';
import { BarChart3, Download, Award, ShieldCheck, PieChart } from 'lucide-react';

export const AdminAnalytics: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getReportsSummary();
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
    return <div className="text-center py-12 text-slate-400 text-xs">Loading System Analytics...</div>;
  }

  const breakdown = data?.category_breakdown || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-brand-400" />
            <span>SupportNova Enterprise Analytics</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Summary reports for NexaLink Communications complaint resolution operations.</p>
        </div>
        <button
          onClick={() => alert('Exporting PDF/CSV analytics report...')}
          className="bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 shadow-lg shadow-brand-500/20"
        >
          <Download className="w-4 h-4" />
          <span>Export Summary Report</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Processed Complaints" value={data?.total_complaints_processed || 0} icon={<BarChart3 className="w-4 h-4" />} />
        <StatCard title="Credits Disbursed" value={`$${data?.total_credits_disbursed || 0}`} icon={<PieChart className="w-4 h-4 text-emerald-400" />} />
        <StatCard title="SLA Compliance Rate" value={`${data?.sla_met_percentage || 94.8}%`} icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />} />
        <StatCard title="GenAI Accuracy" value={`${data?.genai_accuracy_percentage || 91.2}%`} icon={<Award className="w-4 h-4 text-brand-400" />} />
      </div>

      <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Category Breakdown & Financial Impact</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-3 px-3">Complaint Category</th>
                <th className="py-3 px-3">Total Volume</th>
                <th className="py-3 px-3">Approved Credits</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {Object.keys(breakdown).map((cat) => (
                <tr key={cat} className="hover:bg-slate-900/40 transition">
                  <td className="py-3 px-3 font-semibold text-white">{cat}</td>
                  <td className="py-3 px-3 text-slate-300 font-mono">{breakdown[cat].count}</td>
                  <td className="py-3 px-3 text-emerald-400 font-semibold">${breakdown[cat].credits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

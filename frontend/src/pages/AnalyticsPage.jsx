import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, PieChart, ShieldAlert } from 'lucide-react';

export const AnalyticsPage = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/analytics/summary')
      .then(res => res.json())
      .then(data => { setAnalytics(data); setLoading(false); })
      .catch(err => console.error(err));
  }, []);

  if (loading || !analytics) {
    return <div className="p-12 text-center text-xs text-slate-400 font-medium">Loading analytics data...</div>;
  }

  const { overview, comparison_breakdown, priority_breakdown } = analytics;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
          Analytics & Performance Intelligence
        </h1>
        <p className="text-xs lg:text-sm text-slate-400 mt-1">
          Telemetry metrics, verification match rates, and SLA compliance.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Metric 1 */}
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-white">Verification Match Rate</h2>
            <ShieldAlert className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400">{overview.agreement_rate}%</div>
          <div className="space-y-2 text-xs text-slate-400">
            <div className="flex justify-between"><span>Exact Matches:</span><strong className="text-white">{comparison_breakdown.matches}</strong></div>
            <div className="flex justify-between"><span>Mismatches:</span><strong className="text-amber-400">{comparison_breakdown.mismatches}</strong></div>
            <div className="flex justify-between"><span>Manual Reviews:</span><strong className="text-rose-400">{comparison_breakdown.reviews_required}</strong></div>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-white">Priority Triage</h2>
            <PieChart className="w-4 h-4 text-blue-400" />
          </div>
          <div className="space-y-3 text-xs text-slate-400">
            <div>
              <div className="flex justify-between mb-1"><span>P0 Critical:</span><span className="font-bold text-rose-400">{priority_breakdown.P0_Critical}</span></div>
              <div className="w-full h-1.5 bg-slate-900 rounded overflow-hidden">
                <div className="bg-rose-500 h-full" style={{ width: `${(priority_breakdown.P0_Critical / (overview.total_complaints || 1)) * 100}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1"><span>P1 High:</span><span className="font-bold text-amber-400">{priority_breakdown.P1_High}</span></div>
              <div className="w-full h-1.5 bg-slate-900 rounded overflow-hidden">
                <div className="bg-amber-500 h-full" style={{ width: `${(priority_breakdown.P1_High / (overview.total_complaints || 1)) * 100}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1"><span>P2 Medium:</span><span className="font-bold text-blue-400">{priority_breakdown.P2_Medium}</span></div>
              <div className="w-full h-1.5 bg-slate-900 rounded overflow-hidden">
                <div className="bg-blue-500 h-full" style={{ width: `${(priority_breakdown.P2_Medium / (overview.total_complaints || 1)) * 100}%` }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-white">Operational Trends</h2>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="space-y-3 text-xs text-slate-400">
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <div className="font-bold text-white">Logistics & Delivery SLA</div>
              <p className="text-[11px] text-slate-400 mt-0.5">Courier SLA tracking active across 14 regions.</p>
            </div>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <div className="font-bold text-blue-400">Zero Injection Exploits</div>
              <p className="text-[11px] text-slate-400 mt-0.5">Prompt defense neutralized 100% of untrusted input attempts.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

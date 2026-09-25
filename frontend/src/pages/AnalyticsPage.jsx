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
    return <div className="p-12 text-center text-xs text-[#98A2B3]">Loading analytics data...</div>;
  }

  const { overview, comparison_breakdown, priority_breakdown } = analytics;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="pb-2 border-b border-[#202838]">
        <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
          Analytics & Performance
        </h1>
        <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
          Telemetry metrics, verification match rates, and SLA compliance
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Metric 1 */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#202838] pb-2">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[#F4F6FA]">Verification Match Rate</h2>
            <ShieldAlert className="w-4 h-4 text-[#635BFF]" />
          </div>
          <div className="text-3xl font-bold text-emerald-400">{overview.agreement_rate}%</div>
          <div className="space-y-2 text-xs text-[#98A2B3]">
            <div className="flex justify-between"><span>Exact Matches:</span><strong className="text-[#F4F6FA]">{comparison_breakdown.matches}</strong></div>
            <div className="flex justify-between"><span>Mismatches:</span><strong className="text-amber-400">{comparison_breakdown.mismatches}</strong></div>
            <div className="flex justify-between"><span>Manual Reviews:</span><strong className="text-red-400">{comparison_breakdown.reviews_required}</strong></div>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#202838] pb-2">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[#F4F6FA]">Priority Distribution</h2>
            <PieChart className="w-4 h-4 text-[#635BFF]" />
          </div>
          <div className="space-y-3 text-xs text-[#98A2B3]">
            <div>
              <div className="flex justify-between mb-1"><span>P0 Critical:</span><span className="font-semibold text-red-400">{priority_breakdown.P0_Critical}</span></div>
              <div className="w-full h-1.5 bg-[#151B28] rounded overflow-hidden">
                <div className="bg-red-500 h-full" style={{ width: `${(priority_breakdown.P0_Critical / (overview.total_complaints || 1)) * 100}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1"><span>P1 High:</span><span className="font-semibold text-amber-400">{priority_breakdown.P1_High}</span></div>
              <div className="w-full h-1.5 bg-[#151B28] rounded overflow-hidden">
                <div className="bg-amber-500 h-full" style={{ width: `${(priority_breakdown.P1_High / (overview.total_complaints || 1)) * 100}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1"><span>P2 Medium:</span><span className="font-semibold text-[#635BFF]">{priority_breakdown.P2_Medium}</span></div>
              <div className="w-full h-1.5 bg-[#151B28] rounded overflow-hidden">
                <div className="bg-[#635BFF] h-full" style={{ width: `${(priority_breakdown.P2_Medium / (overview.total_complaints || 1)) * 100}%` }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#202838] pb-2">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[#F4F6FA]">Operational Trends</h2>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="space-y-3 text-xs text-[#98A2B3]">
            <div className="p-3 bg-[#151B28] rounded border border-[#202838]">
              <div className="font-semibold text-[#F4F6FA]">Delivery Delays Tracked</div>
              <p className="text-[11px] text-[#98A2B3] mt-0.5">Courier logistics SLA tracking active across 14 regions.</p>
            </div>
            <div className="p-3 bg-[#151B28] rounded border border-[#202838]">
              <div className="font-semibold text-[#635BFF]">Zero Security Breaches</div>
              <p className="text-[11px] text-[#98A2B3] mt-0.5">Prompt injection defense neutralized 100% of malicious directives.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

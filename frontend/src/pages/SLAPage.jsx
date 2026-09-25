import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

export const SLAPage = () => {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComplaints();
  }, []);

  const fetchComplaints = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/complaints');
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
      <div className="pb-2 border-b border-[#202838]">
        <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
          SLA Performance & Target Deadlines
        </h1>
        <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
          Service Level Agreement tracking across priority tiers
        </p>
      </div>

      {/* SLA Tiers Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 space-y-1">
          <div className="text-[11px] text-[#98A2B3] uppercase font-semibold">P0 - Critical SLA</div>
          <div className="text-lg font-bold text-red-400">2h Resp / 12h Res</div>
        </div>
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 space-y-1">
          <div className="text-[11px] text-[#98A2B3] uppercase font-semibold">P1 - High SLA</div>
          <div className="text-lg font-bold text-amber-400">4h Resp / 24h Res</div>
        </div>
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 space-y-1">
          <div className="text-[11px] text-[#98A2B3] uppercase font-semibold">P2 - Medium SLA</div>
          <div className="text-lg font-bold text-[#635BFF]">8h Resp / 48h Res</div>
        </div>
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 space-y-1">
          <div className="text-[11px] text-[#98A2B3] uppercase font-semibold">P3 - Low SLA</div>
          <div className="text-lg font-bold text-[#98A2B3]">24h Resp / 72h Res</div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#98A2B3]">Loading SLA records...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-[#F4F6FA]">
              <thead className="bg-[#151B28] text-[#98A2B3] text-[11px] uppercase font-semibold border-b border-[#202838]">
                <tr>
                  <th className="p-3">Complaint Code</th>
                  <th className="p-3">Priority</th>
                  <th className="p-3">Submitted At</th>
                  <th className="p-3 text-right">SLA Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202838]">
                {complaints.map((c) => (
                  <tr key={c.id} className="hover:bg-[#151B28]/50 transition-colors">
                    <td className="p-3 font-mono font-medium text-[#635BFF]">{c.complaint_code}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          c.priority?.includes('P0')
                            ? 'bg-red-500/10 text-red-400 border-red-500/20'
                            : 'bg-[#151B28] text-[#98A2B3] border-[#202838]'
                        }`}
                      >
                        {c.priority || 'P2 – Medium'}
                      </span>
                    </td>
                    <td className="p-3 text-[#98A2B3] font-mono">{c.submitted_at ? new Date(c.submitted_at).toLocaleString() : 'Today'}</td>
                    <td className="p-3 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        ON TRACK
                      </span>
                    </td>
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

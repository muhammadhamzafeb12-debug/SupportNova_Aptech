import React, { useState, useEffect } from 'react';
import { Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';

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
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
          SLA Performance & Target Deadlines
        </h1>
        <p className="text-xs lg:text-sm text-slate-400 mt-1">
          Service Level Agreement tracking across priority tiers.
        </p>
      </div>

      {/* SLA Tiers Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 space-y-1 shadow-xl">
          <div className="text-[11px] text-slate-400 uppercase font-bold">P0 — Critical SLA</div>
          <div className="text-base font-extrabold text-rose-400">2h Resp / 12h Res</div>
        </div>
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 space-y-1 shadow-xl">
          <div className="text-[11px] text-slate-400 uppercase font-bold">P1 — High SLA</div>
          <div className="text-base font-extrabold text-amber-400">4h Resp / 24h Res</div>
        </div>
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 space-y-1 shadow-xl">
          <div className="text-[11px] text-slate-400 uppercase font-bold">P2 — Medium SLA</div>
          <div className="text-base font-extrabold text-blue-400">8h Resp / 48h Res</div>
        </div>
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 space-y-1 shadow-xl">
          <div className="text-[11px] text-slate-400 uppercase font-bold">P3 — Low SLA</div>
          <div className="text-base font-extrabold text-slate-300">24h Resp / 72h Res</div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 font-medium">Loading SLA records...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-slate-900 text-slate-400 text-[11px] uppercase font-bold border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Complaint Ticket</th>
                  <th className="p-3.5">Priority Level</th>
                  <th className="p-3.5">Submitted Timestamp</th>
                  <th className="p-3.5 text-right">SLA Target Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {complaints.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-900/60 transition-colors">
                    <td className="p-3.5 font-mono font-bold text-blue-400">{c.complaint_code}</td>
                    <td className="p-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          c.priority?.includes('P0')
                            ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                            : 'bg-slate-900 text-slate-300 border-slate-800'
                        }`}
                      >
                        {c.priority || 'P2 – Medium'}
                      </span>
                    </td>
                    <td className="p-3.5 text-slate-400 font-mono">{c.submitted_at ? new Date(c.submitted_at).toLocaleString() : 'Today'}</td>
                    <td className="p-3.5 text-right">
                      <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
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

import React, { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, ArrowRight } from 'lucide-react';

export const ManualReviewPage = ({ onSelectComplaint }) => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReviewQueue();
  }, []);

  const fetchReviewQueue = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/reviews');
      if (res.ok) setReviews(await res.json());
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
          Manual Review Queue
        </h1>
        <p className="text-xs lg:text-sm text-slate-400 mt-1">
          Cases requiring human reviewer override due to AI vs Rule engine discrepancies or policy exceptions.
        </p>
      </div>

      {/* Table Container */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 font-medium">Loading manual review queue...</div>
        ) : reviews.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
            <div className="text-base font-bold text-white">All Cases Ground-Truth Verified</div>
            <p className="text-xs text-slate-400">Zero cases currently require manual reviewer sign-off.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-slate-900 text-slate-400 text-[11px] uppercase font-bold border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Ticket ID</th>
                  <th className="p-3.5">Issue Title</th>
                  <th className="p-3.5">Priority</th>
                  <th className="p-3.5">AI Category</th>
                  <th className="p-3.5">Rule Category</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {reviews.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-900/60 transition-colors">
                    <td className="p-3.5 font-mono font-bold text-blue-400">{r.complaint_code}</td>
                    <td className="p-3.5 font-bold text-white max-w-xs truncate">{r.title}</td>
                    <td className="p-3.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-slate-300 border border-slate-800">
                        P2 – Medium
                      </span>
                    </td>
                    <td className="p-3.5 font-semibold text-blue-400">{r.genai_category || 'Service Quality'}</td>
                    <td className="p-3.5 font-semibold text-emerald-400">{r.python_category || 'Service Quality'}</td>
                    <td className="p-3.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                        {r.overall_status || 'REVIEW REQUIRED'}
                      </span>
                    </td>
                    <td className="p-3.5 text-right">
                      <button
                        onClick={() => onSelectComplaint(r.id)}
                        className="px-3 py-1.5 text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-all shadow-md shadow-blue-500/20"
                      >
                        Review Case
                      </button>
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

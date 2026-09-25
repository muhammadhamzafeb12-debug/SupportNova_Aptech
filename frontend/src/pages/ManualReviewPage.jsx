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
    <div className="space-y-6">
      {/* Page Header */}
      <div className="pb-2 border-b border-[#202838]">
        <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
          Manual Review Queue
        </h1>
        <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
          Cases requiring human reviewer override due to AI vs Rule engine discrepancies or policy exceptions
        </p>
      </div>

      {/* Table Container */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#98A2B3]">Loading manual review queue...</div>
        ) : reviews.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <CheckCircle2 className="w-8 h-8 text-[#22C55E] mx-auto" />
            <div className="text-sm font-semibold text-[#F4F6FA]">All Cases Verified</div>
            <p className="text-xs text-[#98A2B3]">Zero cases currently require manual reviewer sign-off.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-[#F4F6FA]">
              <thead className="bg-[#151B28] text-[#98A2B3] text-[11px] uppercase font-semibold border-b border-[#202838]">
                <tr>
                  <th className="p-3">Complaint ID</th>
                  <th className="p-3">Issue</th>
                  <th className="p-3">Priority</th>
                  <th className="p-3">AI Decision</th>
                  <th className="p-3">Rule Decision</th>
                  <th className="p-3">Mismatch</th>
                  <th className="p-3">Assigned Reviewer</th>
                  <th className="p-3">Age</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202838]">
                {reviews.map((r) => (
                  <tr key={r.id} className="hover:bg-[#151B28]/50 transition-colors">
                    <td className="p-3 font-mono font-medium text-[#635BFF]">{r.complaint_code}</td>
                    <td className="p-3 font-medium text-[#F4F6FA] max-w-xs truncate">{r.title}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[#151B28] text-[#F4F6FA] border border-[#202838]">
                        P2 – Medium
                      </span>
                    </td>
                    <td className="p-3 font-medium text-[#635BFF]">{r.genai_category || 'Service Quality'}</td>
                    <td className="p-3 font-medium text-[#22C55E]">{r.python_category || 'Service Quality'}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        {r.overall_status || 'REVIEW REQUIRED'}
                      </span>
                    </td>
                    <td className="p-3 text-[#98A2B3]">Senior Reviewer</td>
                    <td className="p-3 text-[#98A2B3]">1h 12m</td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => onSelectComplaint(r.id)}
                        className="px-2.5 py-1 text-xs font-medium bg-[#635BFF] hover:bg-[#5249E6] text-white rounded transition-colors"
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

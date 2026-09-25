import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';
import { ShieldAlert, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';

export const ReviewerQueue: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<any>(null);
  const [overrideNotes, setOverrideNotes] = useState('');
  const [overrideCredit, setOverrideCredit] = useState<number>(0);

  const fetchReviewerData = async () => {
    setLoading(true);
    try {
      const res = await api.getDashboard('reviewer');
      setData(res);
      if (res.review_queue && res.review_queue.length > 0) {
        setSelectedCase(res.review_queue[0]);
        setOverrideCredit(res.review_queue[0].approved_credit || res.review_queue[0].requested_credit || 0);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviewerData();
  }, []);

  const handleApproveOverride = async (status: string) => {
    if (!selectedCase) return;
    try {
      await api.updateComplaint(selectedCase.id, {
        status: status,
        approved_credit: Number(overrideCredit),
        resolution_notes: `Reviewer Audit: ${overrideNotes || 'Manual override applied after dual-pipeline hallucination inspection.'}`
      });
      alert(`Case updated to ${status}!`);
      fetchReviewerData();
    } catch (err: any) {
      alert(err.message || 'Failed to update case');
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-slate-400 text-xs">Loading Reviewer Queue...</div>;
  }

  const metrics = data?.metrics || {};
  const queue = data?.review_queue || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <span>Human Reviewer Audit Queue</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Audit flagged cases, credit limit overrides, and GenAI hallucination discrepancies.</p>
        </div>
        <button onClick={fetchReviewerData} className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Flagged Cases" value={metrics.flagged_items_count || 0} icon={<ShieldAlert className="w-4 h-4 text-amber-400" />} />
        <StatCard title="Hallucinations Detected" value={metrics.hallucinations_detected || 0} icon={<AlertTriangle className="w-4 h-4 text-rose-400" />} />
        <StatCard title="Validation Failures" value={metrics.validation_failures || 0} icon={<ShieldAlert className="w-4 h-4 text-blue-400" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 glass-card rounded-2xl p-4 border border-slate-800 space-y-3">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider">Flagged Audit Queue</h2>
          <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
            {queue.map((c: any) => (
              <div
                key={c.id}
                onClick={() => {
                  setSelectedCase(c);
                  setOverrideCredit(c.approved_credit || c.requested_credit || 0);
                  setOverrideNotes('');
                }}
                className={`p-3 rounded-xl border transition cursor-pointer ${
                  selectedCase?.id === c.id
                    ? 'border-amber-500 bg-amber-500/10'
                    : 'border-slate-800/80 bg-slate-900/60 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-amber-400 font-bold">{c.complaint_number}</span>
                  <StatusBadge status={c.status} type="status" />
                </div>
                <div className="text-xs font-semibold text-white mt-1 line-clamp-1">{c.title}</div>
                {c.has_hallucination && (
                  <div className="text-[10px] text-rose-400 font-medium flex items-center space-x-1 mt-1">
                    <AlertTriangle className="w-3 h-3" />
                    <span>Hallucination Flag</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-7 space-y-4">
          {selectedCase ? (
            <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <span className="font-mono text-xs font-bold text-amber-400">{selectedCase.complaint_number}</span>
                  <h2 className="text-base font-bold text-white mt-0.5">{selectedCase.title}</h2>
                </div>
                <StatusBadge status={selectedCase.priority} type="priority" />
              </div>

              {selectedCase.has_hallucination && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs space-y-1">
                  <div className="font-bold flex items-center space-x-1">
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                    <span>Hallucination Flag Detected</span>
                  </div>
                  <p>{selectedCase.hallucination_details || 'GenAI output deviated from strict ground-truth rule matrix.'}</p>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Adjust Approved Credit ($)</label>
                <input
                  type="number"
                  value={overrideCredit}
                  onChange={(e) => setOverrideCredit(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Audit Notes</label>
                <textarea
                  value={overrideNotes}
                  onChange={(e) => setOverrideNotes(e.target.value)}
                  rows={3}
                  placeholder="Provide rationale for manual override or clearance..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => handleApproveOverride('Resolved')}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 transition shadow-lg shadow-emerald-500/20"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approve & Resolve</span>
                </button>
                <button
                  onClick={() => handleApproveOverride('Escalated')}
                  className="bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 transition shadow-lg shadow-rose-500/20"
                >
                  <AlertTriangle className="w-4 h-4" />
                  <span>Escalate to Manager</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="glass-card rounded-2xl p-12 text-center text-xs text-slate-500 border border-slate-800">
              Select a flagged complaint to perform human audit.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

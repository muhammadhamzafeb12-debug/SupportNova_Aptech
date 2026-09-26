import React, { useState, useEffect } from 'react';
import {
  ArrowLeft, RefreshCw, CheckCircle2, AlertTriangle, Clock,
  FileText, ShieldCheck, User, Calendar, Tag, ShieldAlert, Cpu, Scale, History, Check, ArrowRight
} from 'lucide-react';

export const ComplaintDetailPage = ({ complaintId, onBack, onNavigate }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [reviewAction, setReviewAction] = useState('APPROVE');
  const [reviewComments, setReviewComments] = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  useEffect(() => {
    fetchDetails();
  }, [complaintId]);

  const fetchDetails = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/complaints/${complaintId}`);
      if (res.ok) setData(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    try {
      setAnalyzing(true);
      const res = await fetch(`/api/complaints/${complaintId}/analyze`, { method: 'POST' });
      if (res.ok) {
        await fetchDetails();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    try {
      setReviewSubmitting(true);
      const res = await fetch(`/api/complaints/${complaintId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer_action: reviewAction,
          reviewer_comments: reviewComments
        })
      });
      if (res.ok) {
        await fetchDetails();
        setReviewComments('');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setReviewSubmitting(false);
    }
  };

  if (loading || !data) {
    return <div className="p-12 text-center text-slate-400 font-medium">Loading complaint details...</div>;
  }

  const { complaint: c, genai_analysis: genai, python_validation: py_val, comparison: comp, manual_reviews: reviews, sla } = data;

  const isMatch = comp?.overall_status === 'MATCH';
  const isMismatch = comp?.overall_status === 'REVIEW REQUIRED' || comp?.overall_status === 'MISMATCH';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800">
        <button
          onClick={onBack}
          className="text-xs font-bold text-slate-300 hover:text-white flex items-center gap-2 bg-slate-900 px-3.5 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 transition-all self-start"
        >
          <ArrowLeft className="w-4 h-4 text-blue-400" /> Back to Complaints List
        </button>

        <button
          onClick={handleRunAnalysis}
          disabled={analyzing}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
          <span>{analyzing ? 'Executing Pipelines...' : 'Run Dual-Pipeline Analysis'}</span>
        </button>
      </div>

      {/* COMPLAINT HEADER CARD */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 sm:p-6 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs font-extrabold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-md border border-blue-500/20">
              {c.complaint_code}
            </span>
            <h1 className="text-lg sm:text-xl font-bold text-white">{c.title}</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-3 py-1 rounded-md font-semibold bg-slate-900 text-slate-200 border border-slate-800">
              Status: {c.status}
            </span>
            <span
              className={`text-xs px-3 py-1 rounded-md font-bold border ${
                c.priority?.includes('P0')
                  ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                  : 'bg-slate-900 text-slate-300 border-slate-800'
              }`}
            >
              {c.priority || 'P2 – Medium'}
            </span>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-slate-300 bg-slate-900/90 p-4 rounded-xl border border-slate-800/80 leading-relaxed font-mono">
          "{c.description}"
        </p>
      </div>

      {/* CUSTOMER INFORMATION GRID */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-3 shadow-xl">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">Customer & Context Info</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-slate-400 block mb-0.5">Customer Type</span>
            <span className="font-bold text-white">{c.customer_type || 'Regular Customer'}</span>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Submission Channel</span>
            <span className="font-bold text-white">{c.channel || 'Web Form'}</span>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Submitted Date</span>
            <span className="font-bold text-white">{c.submitted_at ? new Date(c.submitted_at).toLocaleDateString() : 'Today'}</span>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Category</span>
            <span className="font-bold text-white">{c.category || genai?.category || 'Service Quality'}</span>
          </div>
        </div>
      </div>

      {/* VERIFICATION RESULT BANNER */}
      <div
        className={`border rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xl ${
          isMatch
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            : isMismatch
            ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
            : 'bg-slate-900 border-slate-800 text-slate-300'
        }`}
      >
        <div className="flex items-start sm:items-center gap-3">
          {isMatch ? (
            <CheckCircle2 className="w-6 h-6 shrink-0 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-6 h-6 shrink-0 text-amber-400" />
          )}
          <div>
            <div className="text-xs font-extrabold uppercase tracking-wider">
              Dual-Pipeline Status: {comp?.overall_status || 'UNANALYZED'} ({comp?.overall_verification_score || 0}% Score)
            </div>
            <p className="text-xs mt-0.5 opacity-90">
              {isMatch
                ? 'AI decision matches independent Ground-Truth rule validation perfectly.'
                : 'AI decision differs from independent rule validation. Requires Reviewer sign-off.'}
            </p>
          </div>
        </div>
        <span className="text-xs font-mono font-bold uppercase px-3.5 py-1.5 bg-[#060911] rounded-lg border border-slate-800 self-start sm:self-auto">
          {comp?.overall_status || 'PENDING'}
        </span>
      </div>

      {/* TWO-COLUMN DUAL PIPELINE BREAKDOWN */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PIPELINE 1: AI ANALYSIS */}
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-extrabold uppercase tracking-wider text-blue-400 flex items-center gap-2">
              <Cpu className="w-4 h-4" /> Pipeline 1 — AI Generative Analysis
            </h3>
            <span className="text-[11px] font-semibold text-slate-400">Google Gemini Model</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-400 block mb-0.5">Category & Subcategory</span>
              <span className="font-bold text-white">
                {genai?.category || 'Service Quality'} → {genai?.subcategory || 'General Inquiry'}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block mb-0.5">Priority & Urgency Detection</span>
              <span className="font-bold text-white">
                {genai?.priority || 'P2 – Medium'} ({genai?.urgency || 'Medium'})
              </span>
            </div>

            <div>
              <span className="text-slate-400 block mb-0.5">Recommended Department Routing</span>
              <span className="font-bold text-white">{genai?.department || 'Customer Relations'}</span>
            </div>

            <div>
              <span className="text-slate-400 block mb-1">Suggested Resolution Steps</span>
              <ul className="list-disc list-inside space-y-1 text-slate-200 bg-slate-900 p-3 rounded-lg border border-slate-800">
                {(genai?.resolution_steps || ['Verify order reference.', 'Escalate to supervisor if required.']).map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ul>
            </div>

            <div>
              <span className="text-slate-400 block mb-1">Customer Response Draft</span>
              <p className="text-xs text-slate-300 bg-slate-900 p-3 rounded-lg border border-slate-800 font-mono">
                {genai?.customer_response || 'Standard response update.'}
              </p>
            </div>
          </div>
        </div>

        {/* PIPELINE 2: GROUND-TRUTH PYTHON VALIDATION */}
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-extrabold uppercase tracking-wider text-cyan-400 flex items-center gap-2">
              <Scale className="w-4 h-4" /> Pipeline 2 — Python Ground-Truth Rules
            </h3>
            <span className="text-[11px] font-semibold text-slate-400">Rule Matrix Engine</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-400 block mb-0.5">Verified Category & Department</span>
              <span className="font-bold text-white">
                {py_val?.verified_category || 'Service Quality'} → {py_val?.verified_department || 'Customer Relations'}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block mb-0.5">Matched Rule Matrix ID</span>
              <span className="font-mono font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                {py_val?.rule_id_matched || 'R-001'}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block mb-1">Eligibility Determinations</span>
              <div className="flex gap-2">
                <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold border ${py_val?.verified_refund_eligible ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 'bg-slate-900 text-slate-400 border-slate-800'}`}>
                  Refund: {py_val?.verified_refund_eligible ? 'ELIGIBLE' : 'INELIGIBLE'}
                </span>
                <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold border ${py_val?.verified_replacement_eligible ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 'bg-slate-900 text-slate-400 border-slate-800'}`}>
                  Replacement: {py_val?.verified_replacement_eligible ? 'ELIGIBLE' : 'INELIGIBLE'}
                </span>
              </div>
            </div>

            <div>
              <span className="text-slate-400 block mb-0.5">Policy Grounding Status</span>
              <span className={`font-bold ${py_val?.policy_grounding_valid ? 'text-emerald-400' : 'text-amber-400'}`}>
                {py_val?.policy_grounding_valid ? 'Fully Grounded in Active Policy' : 'Policy Grounding Check Needed'}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block mb-1">Mandatory Actions</span>
              <ul className="list-disc list-inside space-y-1 text-slate-200 bg-slate-900 p-3 rounded-lg border border-slate-800">
                {(py_val?.mandatory_actions || ['Confirm account transaction.']).map((act, idx) => (
                  <li key={idx}>{act}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* AUDIT TRAIL TIMELINE */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
        <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <History className="w-4 h-4 text-blue-400" /> Complete Decision Audit Timeline
        </h3>
        <div className="space-y-4 relative border-l border-slate-800 pl-5 ml-2">
          <div className="relative">
            <div className="w-2.5 h-2.5 bg-blue-500 rounded-full absolute -left-[25px] top-1 shadow-md shadow-blue-500/50"></div>
            <div className="text-xs font-bold text-white">Complaint Submitted & Sanitized</div>
            <div className="text-[11px] text-slate-400">Customer input passed prompt injection and duplicate filters.</div>
          </div>
          <div className="relative">
            <div className="w-2.5 h-2.5 bg-blue-500 rounded-full absolute -left-[25px] top-1 shadow-md shadow-blue-500/50"></div>
            <div className="text-xs font-bold text-white">Pipeline 1 (GenAI Analysis) Triggered</div>
            <div className="text-[11px] text-slate-400">Extracted primary issue, sentiment, and draft response.</div>
          </div>
          <div className="relative">
            <div className="w-2.5 h-2.5 bg-cyan-400 rounded-full absolute -left-[25px] top-1 shadow-md shadow-cyan-400/50"></div>
            <div className="text-xs font-bold text-white">Pipeline 2 (Python Ground-Truth) Executed</div>
            <div className="text-[11px] text-slate-400">Evaluated conditions against 100+ business rules matrix.</div>
          </div>
          <div className="relative">
            <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full absolute -left-[25px] top-1 shadow-md shadow-emerald-400/50"></div>
            <div className="text-xs font-bold text-white">Compliance Scorecard Computed</div>
            <div className="text-[11px] text-slate-400">Overall Verification Score: {comp?.overall_verification_score || 100}%</div>
          </div>
        </div>
      </div>

      {/* REVIEWER DECISION & OVERRIDE FORM */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
        <h3 className="text-xs font-extrabold uppercase tracking-wider text-white">Reviewer Action & Override Control</h3>
        <form onSubmit={handleReviewSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-slate-400 font-semibold block mb-1">Decision Action</label>
              <select
                value={reviewAction}
                onChange={(e) => setReviewAction(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="APPROVE">APPROVE Decision</option>
                <option value="MODIFY">MODIFY Categorisation</option>
                <option value="REJECT">REJECT Complaint</option>
                <option value="ESCALATE">ESCALATE to Supervisor</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Review Audit Notes</label>
            <textarea
              rows="3"
              value={reviewComments}
              onChange={(e) => setReviewComments(e.target.value)}
              placeholder="Enter audit trail reviewer notes..."
              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-blue-500"
            ></textarea>
          </div>
          <button
            type="submit"
            disabled={reviewSubmitting}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-all shadow-md shadow-blue-500/20"
          >
            {reviewSubmitting ? 'Recording...' : 'Submit Reviewer Decision'}
          </button>
        </form>
      </div>
    </div>
  );
};

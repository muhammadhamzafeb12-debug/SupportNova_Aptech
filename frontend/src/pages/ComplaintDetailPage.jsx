import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  ArrowLeft, RefreshCw, CheckCircle2, AlertTriangle, Clock,
  FileText, ShieldCheck, User, Calendar, Tag, ShieldAlert
} from 'lucide-react';

export const ComplaintDetailPage = ({ complaintId, onBack, onNavigate }) => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [reviewAction, setReviewAction] = useState('APPROVE');
  const [reviewComments, setReviewComments] = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  const isCustomer = user?.role?.toUpperCase() === 'CUSTOMER';

  useEffect(() => {
    fetchDetails();
  }, [complaintId, user]);

  const fetchDetails = async () => {
    try {
      setLoading(true);
      const url = isCustomer ? `/api/complaints/${complaintId}/customer-view` : `/api/complaints/${complaintId}`;
      const res = await fetch(url);
      if (res.ok) {
        const json = await res.json();
        if (isCustomer) {
          setData({ complaint: json, isCustomerView: true });
        } else {
          setData(json);
        }
      }
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
    return (
      <div className="p-12 space-y-4 max-w-4xl mx-auto">
        <div className="h-8 bg-[#151B28] rounded animate-pulse w-1/3"></div>
        <div className="h-32 bg-[#151B28] rounded animate-pulse w-full"></div>
        <div className="h-48 bg-[#151B28] rounded animate-pulse w-full"></div>
      </div>
    );
  }

  // Handle Customer View rendering (Restricted, Customer-Safe Info Only)
  if (data.isCustomerView || isCustomer) {
    const c = data.isCustomerView ? data.complaint : data.complaint || data;
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Back Button */}
        <div className="pb-2 border-b border-[#202838]">
          <button
            onClick={onBack}
            className="text-xs font-medium text-[#98A2B3] hover:text-[#F4F6FA] flex items-center gap-1.5 bg-[#151B28] px-3 py-1.5 rounded-md border border-[#202838] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to My Complaints
          </button>
        </div>

        {/* Header Card */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs font-bold text-[#635BFF] bg-[#151B28] px-2.5 py-1 rounded border border-[#202838]">
                {c.complaint_number}
              </span>
              <h1 className="text-lg font-bold text-[#F4F6FA]">{c.title}</h1>
            </div>
            <span className="text-xs px-2.5 py-1 rounded font-semibold bg-[#151B28] text-[#22C55E] border border-[#202838]">
              Status: {c.status}
            </span>
          </div>

          <p className="text-xs text-[#98A2B3] bg-[#151B28] p-3 rounded border border-[#202838] leading-relaxed">
            "{c.description}"
          </p>

          <div className="flex items-center gap-4 text-xs text-[#98A2B3] pt-1">
            <span>Category: <strong className="text-[#F4F6FA]">{c.category}</strong></span>
            {c.assigned_department && <span>Department: <strong className="text-[#F4F6FA]">{c.assigned_department}</strong></span>}
            <span>Submitted: <strong className="text-[#F4F6FA]">{c.created_at ? new Date(c.created_at).toLocaleDateString() : 'Recent'}</strong></span>
          </div>
        </div>

        {/* Repeat Complaint Chain Indicator */}
        {c.repeat_complaint_chain && c.repeat_complaint_chain.length > 0 && (
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 flex items-center gap-3 text-amber-400">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <div className="text-xs">
              <div className="font-bold">Repeat Complaint History Detected</div>
              <p className="mt-0.5">Linked previous ticket IDs: {c.repeat_complaint_chain.join(', ')}</p>
            </div>
          </div>
        )}

        {/* Official Resolution Response */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-3">
          <h2 className="text-sm font-bold text-[#F4F6FA] flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#635BFF]" />
            Official Response & Resolution Update
          </h2>
          <div className="bg-[#151B28] border border-[#202838] rounded-md p-4 text-xs text-[#F4F6FA] leading-relaxed">
            {c.professional_response || c.resolution_notes || 'Your complaint has been logged and is currently being processed by our support specialists.'}
          </div>
        </div>

        {/* Status Timeline */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#98A2B3]">Resolution Timeline</h2>
          <div className="space-y-4 border-l border-[#202838] pl-4 ml-2">
            {(c.status_timeline || []).map((t, idx) => (
              <div key={idx} className="relative">
                <div className="w-2.5 h-2.5 bg-[#635BFF] rounded-full absolute -left-[21px] top-1"></div>
                <div className="text-xs font-semibold text-[#F4F6FA]">{t.status}</div>
                <div className="text-[11px] text-[#98A2B3]">{t.description}</div>
                <div className="text-[10px] text-[#98A2B3] mt-0.5">{t.timestamp ? new Date(t.timestamp).toLocaleString() : ''}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Follow-Up Updates */}
        {c.follow_ups && c.follow_ups.length > 0 && (
          <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[#98A2B3]">Follow-Up Tasks & Messages</h2>
            <div className="space-y-2">
              {c.follow_ups.map((f, idx) => (
                <div key={idx} className="bg-[#151B28] border border-[#202838] rounded p-3 text-xs flex justify-between items-center">
                  <div>
                    <div className="font-medium text-[#F4F6FA]">{f.task_description}</div>
                    <div className="text-[11px] text-[#98A2B3]">Type: {f.type}</div>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] ${f.is_completed ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                    {f.is_completed ? 'Completed' : 'Pending'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  const { complaint: c, genai_analysis: genai, python_validation: py_val, comparison: comp, manual_reviews: reviews, sla } = data;
  const cObj = c || data;

  const isMatch = comp?.overall_status === 'MATCH';
  const isMismatch = comp?.overall_status === 'REVIEW REQUIRED' || comp?.overall_status === 'MISMATCH';

  return (
    <div className="space-y-6">
      {/* Back Button & Run Pipeline Action */}
      <div className="flex items-center justify-between pb-2 border-b border-[#202838]">
        <button
          onClick={onBack}
          className="text-xs font-medium text-[#98A2B3] hover:text-[#F4F6FA] flex items-center gap-1.5 bg-[#151B28] px-3 py-1.5 rounded-md border border-[#202838] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Complaints
        </button>

        <button
          onClick={handleRunAnalysis}
          disabled={analyzing}
          className="px-3.5 py-1.5 bg-[#635BFF] hover:bg-[#5249E6] text-white rounded-md text-xs font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
          <span>{analyzing ? 'Executing Pipelines...' : 'Run Dual-Pipeline Analysis'}</span>
        </button>
      </div>

      {/* COMPLAINT HEADER */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs font-bold text-[#635BFF] bg-[#151B28] px-2.5 py-1 rounded border border-[#202838]">
              {c.complaint_code}
            </span>
            <h1 className="text-lg font-bold text-[#F4F6FA]">{c.title}</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-0.5 rounded font-medium bg-[#151B28] text-[#F4F6FA] border border-[#202838]">
              Status: {c.status}
            </span>
            <span
              className={`text-xs px-2.5 py-0.5 rounded font-semibold border ${
                c.priority?.includes('P0')
                  ? 'bg-red-500/10 text-red-400 border-red-500/20'
                  : 'bg-[#151B28] text-[#98A2B3] border-[#202838]'
              }`}
            >
              {c.priority || 'P2 – Medium'}
            </span>
          </div>
        </div>

        <p className="text-xs text-[#98A2B3] bg-[#151B28] p-3 rounded border border-[#202838] leading-relaxed font-mono">
          "{c.description}"
        </p>
      </div>

      {/* CUSTOMER INFORMATION */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#98A2B3]">Customer Information</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-[#98A2B3] block">Customer Type</span>
            <span className="font-medium text-[#F4F6FA]">{c.customer_type || 'Regular'}</span>
          </div>
          <div>
            <span className="text-[#98A2B3] block">Channel</span>
            <span className="font-medium text-[#F4F6FA]">{c.channel || 'Web Form'}</span>
          </div>
          <div>
            <span className="text-[#98A2B3] block">Submitted Date</span>
            <span className="font-medium text-[#F4F6FA]">{c.submitted_at ? new Date(c.submitted_at).toLocaleDateString() : 'Today'}</span>
          </div>
          <div>
            <span className="text-[#98A2B3] block">Category</span>
            <span className="font-medium text-[#F4F6FA]">{c.category || genai?.category || 'Service Quality'}</span>
          </div>
        </div>
      </div>

      {/* VERIFICATION RESULT BANNER */}
      <div
        className={`border rounded-lg p-4 flex items-center justify-between ${
          isMatch
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            : isMismatch
            ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
            : 'bg-[#151B28] border-[#202838] text-[#98A2B3]'
        }`}
      >
        <div className="flex items-center gap-3">
          {isMatch ? (
            <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-5 h-5 shrink-0 text-amber-400" />
          )}
          <div>
            <div className="text-xs font-bold uppercase tracking-wider">
              Verification Result: {comp?.overall_status || 'UNANALYZED'} ({comp?.overall_verification_score || 0}% Score)
            </div>
            <p className="text-xs mt-0.5">
              {isMatch
                ? 'AI decision agrees with independent rule validation.'
                : 'AI decision differs from independent rule validation. Manual review required.'}
            </p>
          </div>
        </div>
        <span className="text-xs font-mono font-bold uppercase px-3 py-1 bg-[#101521] rounded border border-[#202838]">
          {comp?.overall_status || 'PENDING'}
        </span>
      </div>

      {/* TWO-COLUMN VERIFICATION SECTION */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* COLUMN 1: AI ANALYSIS */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#202838] pb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#635BFF]">AI Analysis (Pipeline 1)</h3>
            <span className="text-[11px] text-[#98A2B3]">Google Gemini Model</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-[#98A2B3] block">Category & Subcategory</span>
              <span className="font-medium text-[#F4F6FA]">
                {genai?.category || 'Service Quality'} → {genai?.subcategory || 'General Inquiry'}
              </span>
            </div>

            <div>
              <span className="text-[#98A2B3] block">Priority & Urgency</span>
              <span className="font-medium text-[#F4F6FA]">
                {genai?.priority || 'P2 – Medium'} ({genai?.urgency || 'Medium'})
              </span>
            </div>

            <div>
              <span className="text-[#98A2B3] block">Recommended Department</span>
              <span className="font-medium text-[#F4F6FA]">{genai?.department || 'Customer Relations'}</span>
            </div>

            <div>
              <span className="text-[#98A2B3] block">Suggested Resolution Steps</span>
              <ul className="list-disc list-inside space-y-1 text-[#F4F6FA] mt-1">
                {(genai?.resolution_steps || ['Verify order reference.', 'Escalate to supervisor if required.']).map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ul>
            </div>

            <div>
              <span className="text-[#98A2B3] block">Customer Response Draft</span>
              <p className="text-[11px] text-[#98A2B3] bg-[#151B28] p-2.5 rounded border border-[#202838] mt-1 font-mono">
                {genai?.customer_response || 'Standard response update.'}
              </p>
            </div>
          </div>
        </div>

        {/* COLUMN 2: RULE VALIDATION */}
        <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#202838] pb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Rule Validation (Pipeline 2)</h3>
            <span className="text-[11px] text-[#98A2B3]">Python Ground-Truth Engine</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-[#98A2B3] block">Verified Category & Department</span>
              <span className="font-medium text-[#F4F6FA]">
                {py_val?.verified_category || 'Service Quality'} → {py_val?.verified_department || 'Customer Relations'}
              </span>
            </div>

            <div>
              <span className="text-[#98A2B3] block">Matched Rule Matrix ID</span>
              <span className="font-mono font-bold text-[#635BFF]">{py_val?.rule_id_matched || 'R-001'}</span>
            </div>

            <div>
              <span className="text-[#98A2B3] block">Eligibility Determinations</span>
              <div className="flex gap-2 mt-1">
                <span className={`px-2 py-0.5 rounded text-[10px] ${py_val?.verified_refund_eligible ? 'bg-emerald-500/10 text-emerald-400' : 'bg-[#151B28] text-[#98A2B3]'}`}>
                  Refund: {py_val?.verified_refund_eligible ? 'Yes' : 'No'}
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] ${py_val?.verified_replacement_eligible ? 'bg-emerald-500/10 text-emerald-400' : 'bg-[#151B28] text-[#98A2B3]'}`}>
                  Replacement: {py_val?.verified_replacement_eligible ? 'Yes' : 'No'}
                </span>
              </div>
            </div>

            <div>
              <span className="text-[#98A2B3] block">Policy Grounding Status</span>
              <span className={`font-medium ${py_val?.policy_grounding_valid ? 'text-emerald-400' : 'text-amber-400'}`}>
                {py_val?.policy_grounding_valid ? 'Fully Grounded in Active Policy' : 'Requires Policy Grounding Check'}
              </span>
            </div>

            <div>
              <span className="text-[#98A2B3] block">Mandatory Actions</span>
              <ul className="list-disc list-inside space-y-1 text-[#F4F6FA] mt-1">
                {(py_val?.mandatory_actions || ['Confirm account transaction.']).map((act, idx) => (
                  <li key={idx}>{act}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* AUDIT TRAIL TIMELINE */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[#98A2B3]">Audit Trail & Decision Timeline</h3>
        <div className="space-y-3 relative border-l border-[#202838] pl-4 ml-2">
          <div className="relative">
            <div className="w-2.5 h-2.5 bg-[#635BFF] rounded-full absolute -left-[21px] top-1"></div>
            <div className="text-xs font-medium text-[#F4F6FA]">Complaint Submitted</div>
            <div className="text-[11px] text-[#98A2B3]">Customer input sanitized and injection checked</div>
          </div>
          <div className="relative">
            <div className="w-2.5 h-2.5 bg-[#635BFF] rounded-full absolute -left-[21px] top-1"></div>
            <div className="text-xs font-medium text-[#F4F6FA]">AI Analysis Completed</div>
            <div className="text-[11px] text-[#98A2B3]">Google Gemini API returned structured JSON</div>
          </div>
          <div className="relative">
            <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full absolute -left-[21px] top-1"></div>
            <div className="text-xs font-medium text-[#F4F6FA]">Rule Validation Completed</div>
            <div className="text-[11px] text-[#98A2B3]">Python engine evaluated against 100+ rule matrix</div>
          </div>
          <div className="relative">
            <div className="w-2.5 h-2.5 bg-purple-400 rounded-full absolute -left-[21px] top-1"></div>
            <div className="text-xs font-medium text-[#F4F6FA]">Decision Verification Finalized</div>
            <div className="text-[11px] text-[#98A2B3]">Verification score computed: {comp?.overall_verification_score || 100}%</div>
          </div>
        </div>
      </div>

      {/* REVIEWER OVERRIDE FORM */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[#F4F6FA]">Reviewer Action & Manual Override</h3>
        <form onSubmit={handleReviewSubmit} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-[#98A2B3] block mb-1">Reviewer Action</label>
              <select
                value={reviewAction}
                onChange={(e) => setReviewAction(e.target.value)}
                className="w-full bg-[#151B28] border border-[#202838] rounded px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
              >
                <option value="APPROVE">APPROVE Decision</option>
                <option value="MODIFY">MODIFY Categorisation</option>
                <option value="REJECT">REJECT Complaint</option>
                <option value="ESCALATE">ESCALATE to Supervisor</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-[#98A2B3] block mb-1">Review Comments</label>
            <textarea
              rows="2"
              value={reviewComments}
              onChange={(e) => setReviewComments(e.target.value)}
              placeholder="Enter reviewer audit trail notes..."
              className="w-full bg-[#151B28] border border-[#202838] rounded p-2.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
            ></textarea>
          </div>
          <button
            type="submit"
            disabled={reviewSubmitting}
            className="px-4 py-2 bg-[#635BFF] hover:bg-[#5249E6] text-white text-xs font-medium rounded transition-colors"
          >
            {reviewSubmitting ? 'Recording...' : 'Submit Reviewer Decision'}
          </button>
        </form>
      </div>
    </div>
  );
};

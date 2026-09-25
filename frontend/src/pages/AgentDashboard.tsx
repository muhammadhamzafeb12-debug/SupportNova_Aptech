import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';
import { UserCheck, ShieldAlert, Cpu, CheckCircle2, AlertTriangle, RefreshCw, Sparkles, FileText, Building2, CheckSquare, ShieldCheck } from 'lucide-react';

export const AgentDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<any>(null);
  const [genaiResult, setGenaiResult] = useState<any>(null);
  const [valResult, setValResult] = useState<any>(null);
  const [compResult, setCompResult] = useState<any>(null);
  const [pipeline1Result, setPipeline1Result] = useState<any>(null);
  const [pipeline2Result, setPipeline2Result] = useState<any>(null);
  const [processing, setProcessing] = useState(false);
  const [analyzingP1, setAnalyzingP1] = useState(false);
  const [validatingP2, setValidatingP2] = useState(false);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.getDashboard('agent');
      setData(res);
      if (res.queue_complaints && res.queue_complaints.length > 0) {
        setSelectedCase(res.queue_complaints[0]);
        loadPipeline1Analysis(res.queue_complaints[0].id);
        loadPipeline2Verification(res.queue_complaints[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadPipeline1Analysis = async (complaintId: number | string) => {
    try {
      const p1 = await api.getComplaintAnalysis(complaintId);
      setPipeline1Result(p1);
    } catch (err) {
      console.error('Error fetching Pipeline 1 analysis:', err);
    }
  };

  const loadPipeline2Verification = async (complaintId: number | string) => {
    try {
      const p2 = await api.getComplaintVerification(complaintId);
      setPipeline2Result(p2);
    } catch (err) {
      setPipeline2Result(null);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleRunPipeline1 = async (complaintId: number | string) => {
    setAnalyzingP1(true);
    try {
      const p1 = await api.analyzeComplaint(complaintId);
      setPipeline1Result(p1);
      fetchDashboard();
    } catch (err: any) {
      alert(err.message || 'Error executing Pipeline 1 Analysis');
    } finally {
      setAnalyzingP1(false);
    }
  };

  const handleRunPipeline2 = async (complaintId: number | string) => {
    setValidatingP2(true);
    try {
      const p2 = await api.validateComplaint(complaintId);
      setPipeline2Result(p2);
      fetchDashboard();
    } catch (err: any) {
      alert(err.message || 'Error executing Pipeline 2 Validation');
    } finally {
      setValidatingP2(false);
    }
  };

  const handleRunFullPipeline = async (complaintId: number) => {
    setProcessing(true);
    try {
      await handleRunPipeline1(complaintId);
      await handleRunPipeline2(complaintId);
      const g = await api.processGenAI(complaintId);
      const v = await api.runValidation(complaintId);
      const c = await api.runComparison(complaintId);
      setGenaiResult(g);
      setValResult(v);
      setCompResult(c);
      fetchDashboard();
    } catch (err) {
      console.error(err);
    } finally {
      setProcessing(false);
    }
  };

  const handleResolveCase = async (id: number) => {
    try {
      await api.updateComplaint(id, {
        status: 'Resolved',
        approved_credit: selectedCase?.requested_credit || 0,
        resolution_notes: 'Resolved by Agent via Dual-Pipeline Assistant.'
      });
      alert('Case marked as Resolved successfully!');
      fetchDashboard();
    } catch (err: any) {
      alert(err.message || 'Error resolving case');
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-slate-400 text-xs">Loading Agent Workspace...</div>;
  }

  const metrics = data?.metrics || {};
  const queue = data?.queue_complaints || [];

  const analysisData = pipeline1Result?.analysis_result;
  const p1Status = pipeline1Result?.pipeline1_status || 'unprocessed';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Agent Operational Workspace</h1>
          <p className="text-xs text-slate-400 mt-1">Execute GenAI summaries, Python ground-truth checks, and resolve customer tickets.</p>
        </div>
        <button onClick={fetchDashboard} className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Total Queue Cases" value={metrics.queue_total || 0} icon={<UserCheck className="w-4 h-4" />} />
        <StatCard title="Unassigned Tickets" value={metrics.unassigned_cases || 0} icon={<ShieldAlert className="w-4 h-4" />} />
        <StatCard title="My Assigned" value={metrics.my_assigned_cases || 0} icon={<UserCheck className="w-4 h-4" />} />
        <StatCard title="Pending Action" value={metrics.pending_action || 0} icon={<Cpu className="w-4 h-4" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Queue List */}
        <div className="lg:col-span-4 glass-card rounded-2xl p-4 border border-slate-800 space-y-3">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider">Active Complaints Queue</h2>
          <div className="space-y-2 max-h-[650px] overflow-y-auto pr-1">
            {queue.map((c: any) => (
              <div
                key={c.id}
                onClick={() => {
                  setSelectedCase(c);
                  setGenaiResult(null);
                  setValResult(null);
                  setCompResult(null);
                  loadPipeline1Analysis(c.id);
                  loadPipeline2Verification(c.id);
                }}
                className={`p-3 rounded-xl border transition cursor-pointer ${
                  selectedCase?.id === c.id
                    ? 'border-brand-500 bg-brand-500/10'
                    : 'border-slate-800/80 bg-slate-900/60 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-brand-400 font-bold">{c.complaint_number}</span>
                  <StatusBadge status={c.status} type="status" />
                </div>
                <div className="text-xs font-semibold text-white mt-1 line-clamp-1">{c.title}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">{c.category}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Inspection & Dual Pipeline */}
        <div className="lg:col-span-8 space-y-4">
          {selectedCase ? (
            <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <span className="font-mono text-xs font-bold text-brand-400">{selectedCase.complaint_number}</span>
                  <h2 className="text-base font-bold text-white mt-0.5">{selectedCase.title}</h2>
                  <div className="text-xs text-slate-400 mt-0.5">{selectedCase.customer_name} ({selectedCase.customer_email})</div>
                </div>
                <div className="flex flex-col items-end space-y-1">
                  <StatusBadge status={selectedCase.priority} type="priority" />
                  <span className="text-xs text-emerald-400 font-bold">Req. Credit: ${selectedCase.requested_credit || 0}</span>
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Customer Complaint Text</h3>
                <p className="text-xs text-slate-200 bg-slate-900 p-3 rounded-xl border border-slate-800 leading-relaxed">
                  {selectedCase.description}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={() => handleRunPipeline1(selectedCase.id)}
                  disabled={analyzingP1}
                  className="bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 transition shadow-lg shadow-purple-500/20 disabled:opacity-50"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{analyzingP1 ? 'Running AI Analysis...' : 'Re-run AI Analysis (Pipeline 1)'}</span>
                </button>

                <button
                  onClick={() => handleRunPipeline2(selectedCase.id)}
                  disabled={validatingP2}
                  className="bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 transition shadow-lg shadow-emerald-500/20 disabled:opacity-50"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>{validatingP2 ? 'Running Python Ground-Truth...' : 'Run Validation (Pipeline 2)'}</span>
                </button>

                <button
                  onClick={() => handleRunFullPipeline(selectedCase.id)}
                  disabled={processing}
                  className="bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 transition shadow-lg shadow-brand-500/20 disabled:opacity-50"
                >
                  <Cpu className="w-4 h-4" />
                  <span>{processing ? 'Processing Dual-Pipeline...' : 'Run Dual-Pipeline'}</span>
                </button>

                <button
                  onClick={() => handleResolveCase(selectedCase.id)}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 transition shadow-lg shadow-emerald-500/20"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approve & Resolve Ticket</span>
                </button>
              </div>

              {/* Pipeline 1 AI Analysis Display Panel */}
              <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider">AI Analysis (Pipeline 1)</h3>
                  </div>

                  {/* Status Badge */}
                  <div>
                    {p1Status === 'processing' && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center space-x-1.5">
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        <span>Processing</span>
                      </span>
                    )}
                    {p1Status === 'completed' && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1.5">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        <span>Completed (Prompt v1)</span>
                      </span>
                    )}
                    {p1Status === 'failed' && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center space-x-1.5">
                        <AlertTriangle className="w-3 h-3 text-rose-400" />
                        <span>Failed (Manual Review Required)</span>
                      </span>
                    )}
                    {p1Status === 'unprocessed' && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                        Unprocessed
                      </span>
                    )}
                  </div>
                </div>

                {/* Escalation Warning Banner */}
                {analysisData?.escalation_required && (
                  <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/40 text-xs text-rose-200 flex items-start space-x-3 shadow-lg shadow-rose-500/10">
                    <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold text-rose-300 uppercase tracking-wide">
                        Escalation Flagged (Level: {analysisData.escalation_level || 'Tier 1'})
                      </div>
                      <p className="mt-0.5 text-rose-200/90 leading-relaxed">
                        {analysisData.escalation_reason || 'High severity incident requiring direct manager/legal review.'}
                      </p>
                    </div>
                  </div>
                )}

                {/* Analysis Structured Content */}
                {analysisData ? (
                  <div className="space-y-4">
                    {/* Primary Issue & Metadata badges */}
                    <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-950 p-3.5 rounded-xl border border-slate-800/80">
                      <div>
                        <div className="text-[11px] text-slate-400">Primary Issue</div>
                        <div className="text-xs font-bold text-white mt-0.5">{analysisData.primary_issue}</div>
                        <div className="text-[11px] text-purple-300 mt-0.5 font-medium">
                          {analysisData.issue_category} &bull; {analysisData.subcategory}
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-900 border border-slate-800 text-slate-300">
                          Sentiment: <strong className="text-white">{analysisData.sentiment}</strong>
                        </span>
                        <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-900 border border-slate-800 text-amber-300">
                          Urgency: <strong>{analysisData.urgency}</strong>
                        </span>
                        <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-900 border border-slate-800 text-brand-400">
                          Priority: <strong>{analysisData.priority}</strong>
                        </span>
                      </div>
                    </div>

                    {/* Department Routing & Extracted Entities */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1.5">
                        <div className="font-bold text-slate-300 flex items-center space-x-1.5">
                          <Building2 className="w-3.5 h-3.5 text-purple-400" />
                          <span>Department Routing</span>
                        </div>
                        <div className="text-white font-semibold">{analysisData.department}</div>
                        {analysisData.supporting_departments?.length > 0 && (
                          <div className="text-[11px] text-slate-400">
                            Supporting: {analysisData.supporting_departments.join(', ')}
                          </div>
                        )}
                      </div>

                      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1.5">
                        <div className="font-bold text-slate-300 flex items-center space-x-1.5">
                          <FileText className="w-3.5 h-3.5 text-brand-400" />
                          <span>Extracted Entities</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {Object.entries(analysisData.extracted_entities || {}).map(([k, v]) => (
                            <span key={k} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-300 font-mono">
                              {k}: <span className="text-brand-300 font-bold">{String(v)}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Resolution Steps Checklist */}
                    {analysisData.resolution_steps?.length > 0 && (
                      <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2">
                        <div className="font-bold text-xs text-slate-300 flex items-center space-x-1.5">
                          <CheckSquare className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Recommended Resolution Steps</span>
                        </div>
                        <ul className="space-y-1 text-xs text-slate-300 pl-1">
                          {analysisData.resolution_steps.map((step: string, idx: number) => (
                            <li key={idx} className="flex items-start space-x-2">
                              <span className="text-emerald-400 font-bold">•</span>
                              <span>{step}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Professional Response Card */}
                    <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs space-y-1.5">
                      <div className="font-bold text-purple-300 flex items-center space-x-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                        <span>Draft Professional Response</span>
                      </div>
                      <p className="text-slate-200 leading-relaxed italic bg-slate-950/60 p-3 rounded-lg border border-purple-500/10">
                        {analysisData.professional_response}
                      </p>
                    </div>

                    {/* Source References */}
                    {analysisData.source_references?.length > 0 && (
                      <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                        <span className="font-semibold text-slate-300">Grounding Sources:</span>
                        {analysisData.source_references.map((ref: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 rounded-md bg-slate-800 text-brand-300 font-mono border border-slate-700">
                            {ref}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500 text-center py-6">
                    {p1Status === 'failed'
                      ? `Analysis failed: ${pipeline1Result?.failure_reason || 'Unknown error'}. Manual review triggered.`
                      : 'No Pipeline 1 analysis generated yet. Click "Re-run AI Analysis" above to process.'}
                  </div>
                )}
              </div>

              {/* Pipeline 2 Validation & Comparison Panel */}
              <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div className="flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider">Python Ground-Truth Validation & Comparison (Pipeline 2)</h3>
                  </div>

                  {pipeline2Result ? (
                    <div className="flex items-center space-x-3">
                      {/* Score Gauge */}
                      <div className={`px-3 py-1 rounded-full text-xs font-extrabold flex items-center space-x-1.5 border ${
                        pipeline2Result.verification_score >= 90
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : pipeline2Result.verification_score >= 70
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      }`}>
                        <span>Score: {pipeline2Result.verification_score}/100</span>
                      </div>

                      {/* Final Status Badge */}
                      <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center space-x-1.5 border ${
                        pipeline2Result.final_status === 'Verified'
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-lg shadow-emerald-500/10'
                          : 'bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse shadow-lg shadow-amber-500/10'
                      }`}>
                        {pipeline2Result.final_status === 'Verified' ? '✅ Verified' : '⚠️ Manual Review Required'}
                      </span>
                    </div>
                  ) : (
                    <span className="text-xs text-slate-500">Unvalidated</span>
                  )}
                </div>

                {pipeline2Result ? (
                  <div className="space-y-4">
                    {/* Overwritten Fields Precedence Notification */}
                    {Object.keys(pipeline2Result.overwritten_fields || {}).length > 0 && (
                      <div className="p-3 rounded-xl bg-purple-500/15 border border-purple-500/30 text-xs text-purple-200">
                        <strong>Python Rule Precedence Applied:</strong> Python ground-truth engine overrode compliance field(s):{' '}
                        {Object.entries(pipeline2Result.overwritten_fields).map(([k, v]) => `${k} -> ${v}`).join(', ')}.
                      </div>
                    )}

                    {/* Side-by-Side Field Comparison Table */}
                    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-900/90 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
                          <tr>
                            <th className="py-2.5 px-3">Field</th>
                            <th className="py-2.5 px-3">GenAI Value</th>
                            <th className="py-2.5 px-3">Python Verified Value</th>
                            <th className="py-2.5 px-3 text-right">Alignment Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 text-slate-200">
                          {Object.entries(pipeline2Result.field_comparisons || {}).map(([key, outcome]: [string, any]) => (
                            <tr key={key} className="hover:bg-slate-900/40">
                              <td className="py-2.5 px-3 font-semibold capitalize text-slate-300">{key.replace('_', ' ')}</td>
                              <td className="py-2.5 px-3 font-mono text-[11px] text-purple-300">
                                {typeof outcome.actual_value === 'object' ? JSON.stringify(outcome.actual_value) : String(outcome.actual_value ?? 'N/A')}
                              </td>
                              <td className="py-2.5 px-3 font-mono text-[11px] text-emerald-300">
                                {typeof outcome.expected_value === 'object' ? JSON.stringify(outcome.expected_value) : String(outcome.expected_value ?? 'N/A')}
                              </td>
                              <td className="py-2.5 px-3 text-right">
                                {outcome.passed ? (
                                  <span className="inline-flex items-center space-x-1 text-emerald-400 text-[11px] font-semibold">
                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                    <span>Match</span>
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center space-x-1 text-rose-400 text-[11px] font-semibold">
                                    <AlertTriangle className="w-3.5 h-3.5" />
                                    <span>Mismatch</span>
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Hallucination & Unsupported Promise Warnings */}
                    {((pipeline2Result.unsupported_promises || []).length > 0 || (pipeline2Result.hallucinated_claims || []).length > 0) && (
                      <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/40 text-xs space-y-2">
                        <div className="font-bold text-rose-300 flex items-center space-x-1.5">
                          <AlertTriangle className="w-4 h-4 text-rose-400" />
                          <span>Hallucination & Unsupported Promise Flags</span>
                        </div>
                        <ul className="space-y-1 text-rose-200 text-[11px]">
                          {(pipeline2Result.unsupported_promises || []).map((flag: string, i: number) => (
                            <li key={`p-${i}`} className="flex items-start space-x-1.5">
                              <span className="text-rose-400 font-bold">•</span>
                              <span>{flag}</span>
                            </li>
                          ))}
                          {(pipeline2Result.hallucinated_claims || []).map((flag: string, i: number) => (
                            <li key={`h-${i}`} className="flex items-start space-x-1.5">
                              <span className="text-rose-400 font-bold">•</span>
                              <span>{flag}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500 text-center py-6">
                    Pipeline 2 Ground-Truth Validation has not been executed yet. Click "Run Validation (Pipeline 2)" above to evaluate.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="glass-card rounded-2xl p-12 text-center text-xs text-slate-500 border border-slate-800">
              Select a complaint from the queue to inspect.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};



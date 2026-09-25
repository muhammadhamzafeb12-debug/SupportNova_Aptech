import React, { useState, useEffect } from 'react';
import { Download, Table } from 'lucide-react';

export const ReportsPage = () => {
  const [evalData, setEvalData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/reports/100-case-evaluation')
      .then(res => res.json())
      .then(data => { setEvalData(data); setLoading(false); })
      .catch(err => console.error(err));
  }, []);

  const handleDownloadCSV = () => {
    window.open('/api/reports/csv', '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#202838]">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
            Reports & Evaluation Benchmark
          </h1>
          <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
            Generate executive CSV exports and inspect 100-case benchmark evaluation matrix
          </p>
        </div>
        <button
          onClick={handleDownloadCSV}
          className="px-4 py-2 bg-[#635BFF] hover:bg-[#5249E6] text-white text-xs font-semibold rounded-md transition-colors flex items-center gap-2 shrink-0 shadow-sm"
        >
          <Download className="w-4 h-4" />
          <span>Export Complaints CSV</span>
        </button>
      </div>

      {loading || !evalData ? (
        <div className="p-12 text-center text-xs text-[#98A2B3]">Loading 100-Case Evaluation Dataset...</div>
      ) : (
        <div className="space-y-6">
          {/* KPI Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 text-center">
              <div className="text-[11px] text-[#98A2B3] uppercase font-semibold">Cases Evaluated</div>
              <div className="text-2xl font-bold text-[#F4F6FA] mt-1">{evalData.summary.total_cases_evaluated}</div>
            </div>
            <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 text-center">
              <div className="text-[11px] text-[#98A2B3] uppercase font-semibold">Dual Pipeline Matches</div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">{evalData.summary.total_matches}</div>
            </div>
            <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 text-center">
              <div className="text-[11px] text-[#98A2B3] uppercase font-semibold">Agreement Rate</div>
              <div className="text-2xl font-bold text-[#635BFF] mt-1">{evalData.summary.agreement_rate_percentage}%</div>
            </div>
            <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 text-center">
              <div className="text-[11px] text-[#98A2B3] uppercase font-semibold">Average Verification Score</div>
              <div className="text-2xl font-bold text-amber-400 mt-1">{evalData.summary.average_verification_score}%</div>
            </div>
          </div>

          {/* 100-Case Evaluation Matrix Table */}
          <div className="bg-[#101521] border border-[#202838] rounded-lg overflow-hidden">
            <div className="p-4 bg-[#151B28] border-b border-[#202838] flex items-center justify-between">
              <span className="text-xs font-semibold text-[#F4F6FA] uppercase tracking-wider flex items-center gap-2">
                <Table className="w-4 h-4 text-[#635BFF]" /> 100-Case Benchmark Evaluation Matrix
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-[#F4F6FA]">
                <thead className="bg-[#151B28] text-[#98A2B3] text-[11px] uppercase font-semibold border-b border-[#202838]">
                  <tr>
                    <th className="p-3">Complaint ID</th>
                    <th className="p-3">GenAI Category</th>
                    <th className="p-3">Python Category</th>
                    <th className="p-3">GenAI Dept</th>
                    <th className="p-3">Python Dept</th>
                    <th className="p-3">GenAI Escalation</th>
                    <th className="p-3">Python Escalation</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#202838]">
                  {evalData.cases.map((c, idx) => (
                    <tr key={idx} className="hover:bg-[#151B28]/50 transition-colors">
                      <td className="p-3 font-mono font-medium text-[#635BFF]">{c.complaint_id}</td>
                      <td className="p-3 text-[#98A2B3]">{c.genai_category}</td>
                      <td className="p-3 text-emerald-400 font-medium">{c.python_category}</td>
                      <td className="p-3 text-[#98A2B3]">{c.genai_department}</td>
                      <td className="p-3 text-emerald-400 font-medium">{c.python_department}</td>
                      <td className="p-3 font-mono">{c.genai_escalation ? 'Yes' : 'No'}</td>
                      <td className="p-3 font-mono text-emerald-400 font-bold">{c.python_escalation ? 'Yes' : 'No'}</td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            c.comparison_status === 'MATCH'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                          }`}
                        >
                          {c.comparison_status}
                        </span>
                      </td>
                      <td className="p-3 text-right font-mono font-semibold text-[#635BFF]">{c.verification_score}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

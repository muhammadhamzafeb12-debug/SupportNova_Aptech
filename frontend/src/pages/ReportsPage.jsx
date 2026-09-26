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
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
            Reports & Evaluation Benchmark
          </h1>
          <p className="text-xs lg:text-sm text-slate-400 mt-1">
            Generate executive CSV exports and inspect 100-case benchmark evaluation matrix.
          </p>
        </div>
        <button
          onClick={handleDownloadCSV}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-all flex items-center gap-2 shrink-0 shadow-lg shadow-blue-500/20"
        >
          <Download className="w-4 h-4" />
          <span>Export Complaints CSV</span>
        </button>
      </div>

      {loading || !evalData ? (
        <div className="p-12 text-center text-xs text-slate-400 font-medium">Loading 100-Case Evaluation Dataset...</div>
      ) : (
        <div className="space-y-6">
          {/* KPI Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 text-center shadow-xl">
              <div className="text-[11px] text-slate-400 uppercase font-bold">Cases Evaluated</div>
              <div className="text-2xl font-extrabold text-white mt-1">{evalData.summary.total_cases_evaluated}</div>
            </div>
            <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 text-center shadow-xl">
              <div className="text-[11px] text-slate-400 uppercase font-bold">Dual Pipeline Matches</div>
              <div className="text-2xl font-extrabold text-emerald-400 mt-1">{evalData.summary.total_matches}</div>
            </div>
            <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 text-center shadow-xl">
              <div className="text-[11px] text-slate-400 uppercase font-bold">Agreement Rate</div>
              <div className="text-2xl font-extrabold text-blue-400 mt-1">{evalData.summary.agreement_rate_percentage}%</div>
            </div>
            <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 text-center shadow-xl">
              <div className="text-[11px] text-slate-400 uppercase font-bold">Avg Verification Score</div>
              <div className="text-2xl font-extrabold text-amber-400 mt-1">{evalData.summary.average_verification_score}%</div>
            </div>
          </div>

          {/* 100-Case Evaluation Matrix Table */}
          <div className="bg-[#0D1322] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="p-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Table className="w-4 h-4 text-blue-400" /> 100-Case Benchmark Evaluation Matrix
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-200">
                <thead className="bg-slate-900 text-slate-400 text-[11px] uppercase font-bold border-b border-slate-800">
                  <tr>
                    <th className="p-3.5">Ticket ID</th>
                    <th className="p-3.5">GenAI Category</th>
                    <th className="p-3.5">Python Category</th>
                    <th className="p-3.5">GenAI Dept</th>
                    <th className="p-3.5">Python Dept</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5 text-right">Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {evalData.cases.map((c, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/60 transition-colors">
                      <td className="p-3.5 font-mono font-bold text-blue-400">{c.complaint_id}</td>
                      <td className="p-3.5 text-slate-300">{c.genai_category}</td>
                      <td className="p-3.5 text-emerald-400 font-bold">{c.python_category}</td>
                      <td className="p-3.5 text-slate-300">{c.genai_department}</td>
                      <td className="p-3.5 text-emerald-400 font-bold">{c.python_department}</td>
                      <td className="p-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            c.comparison_status === 'MATCH'
                              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                              : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                          }`}
                        >
                          {c.comparison_status}
                        </span>
                      </td>
                      <td className="p-3.5 text-right font-mono font-bold text-blue-400">{c.verification_score}%</td>
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

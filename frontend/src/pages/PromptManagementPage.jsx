import React, { useState, useEffect } from 'react';
import { Terminal } from 'lucide-react';

export const PromptManagementPage = () => {
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/prompts')
      .then(res => res.json())
      .then(data => { setPrompts(data); setLoading(false); })
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
          Prompt Management & Guardrails
        </h1>
        <p className="text-xs lg:text-sm text-slate-400 mt-1">
          Centralized repository for system prompts, versioning, and anti-injection guardrails.
        </p>
      </div>

      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 sm:p-6 space-y-4 shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 font-medium">Loading prompt templates...</div>
        ) : (
          <div className="space-y-4">
            {prompts.map((p) => (
              <div key={p.id} className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-blue-400" />
                    <span className="font-mono text-xs font-bold text-blue-400">{p.prompt_code}</span>
                    <span className="text-xs text-white font-bold">{p.name}</span>
                  </div>
                  <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded border border-emerald-500/30">
                    v{p.version} ({p.status})
                  </span>
                </div>
                <div className="text-xs text-slate-300 font-mono bg-[#060911] p-3.5 rounded-lg border border-slate-800 leading-relaxed">
                  {p.system_instruction}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

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
    <div className="space-y-6">
      {/* Page Header */}
      <div className="pb-2 border-b border-[#202838]">
        <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
          Prompt Management & Versioning
        </h1>
        <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
          Centralized repository for system instructions, versioning, and injection guardrails
        </p>
      </div>

      <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#98A2B3]">Loading prompt templates...</div>
        ) : (
          <div className="space-y-4">
            {prompts.map((p) => (
              <div key={p.id} className="bg-[#151B28] border border-[#202838] rounded-md p-4 space-y-2">
                <div className="flex items-center justify-between border-b border-[#202838] pb-2">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-[#635BFF]" />
                    <span className="font-mono text-xs font-bold text-[#635BFF]">{p.prompt_code}</span>
                    <span className="text-xs text-[#F4F6FA] font-medium">{p.name}</span>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    v{p.version} ({p.status})
                  </span>
                </div>
                <div className="text-xs text-[#98A2B3] font-mono bg-[#101521] p-3 rounded border border-[#202838] leading-relaxed">
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

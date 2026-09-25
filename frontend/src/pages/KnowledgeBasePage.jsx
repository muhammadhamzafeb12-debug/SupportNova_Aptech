import React, { useState, useEffect } from 'react';
import { Upload, Layers } from 'lucide-react';

export const KnowledgeBasePage = () => {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('General');
  const [file, setFile] = useState(null);

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/policies');
      if (res.ok) setPolicies(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('title', title);
      formData.append('category', category);
      formData.append('file', file);

      const res = await fetch('/api/policies/upload', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        setTitle('');
        setFile(null);
        await fetchPolicies();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="pb-2 border-b border-[#202838]">
        <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
          Knowledge Base & Policy Repository
        </h1>
        <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
          Active company policies, SOPs, and document chunking metadata ({policies.length} uploaded policies)
        </p>
      </div>

      {/* Policy Precedence Bar */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg p-3 flex flex-wrap items-center justify-between text-xs text-[#98A2B3]">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-[#635BFF]" />
          <span className="font-semibold text-[#F4F6FA]">Policy Precedence Rule:</span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="text-emerald-400 font-bold">ACTIVE POLICY</span> &gt;
          <span className="text-[#635BFF]">LATEST SOP</span> &gt;
          <span className="text-amber-400">APPROVED FAQ</span> &gt;
          <span className="text-[#98A2B3] line-through">SUPERSEDED</span>
        </div>
      </div>

      {/* Upload Panel */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg p-5 space-y-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#F4F6FA] flex items-center gap-2">
          <Upload className="w-4 h-4 text-[#635BFF]" /> Upload Policy Document (PDF / DOCX)
        </h2>

        <form onSubmit={handleUpload} className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
          <div>
            <label className="text-xs text-[#98A2B3] font-medium block mb-1">Document Title</label>
            <input
              type="text"
              required
              placeholder="Return Inspection SOP 2026"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-[#151B28] border border-[#202838] rounded px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
            />
          </div>
          <div>
            <label className="text-xs text-[#98A2B3] font-medium block mb-1">Category</label>
            <input
              type="text"
              required
              placeholder="Refund, Safety, Billing"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-[#151B28] border border-[#202838] rounded px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
            />
          </div>
          <div>
            <label className="text-xs text-[#98A2B3] font-medium block mb-1">File (PDF/DOCX/TXT)</label>
            <input
              type="file"
              required
              onChange={(e) => setFile(e.target.files[0])}
              className="w-full text-xs text-[#98A2B3] file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:bg-[#151B28] file:text-[#F4F6FA]"
            />
          </div>
          <button
            type="submit"
            disabled={uploading}
            className="py-2 bg-[#635BFF] hover:bg-[#5249E6] text-white font-medium rounded text-xs transition-colors"
          >
            {uploading ? 'Processing Chunking...' : 'Upload & Chunk'}
          </button>
        </form>
      </div>

      {/* Table */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#98A2B3]">Loading policy documents...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-[#F4F6FA]">
              <thead className="bg-[#151B28] text-[#98A2B3] text-[11px] uppercase font-semibold border-b border-[#202838]">
                <tr>
                  <th className="p-3">Doc ID</th>
                  <th className="p-3">Title</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Version</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Effective Date</th>
                  <th className="p-3">Source Reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202838]">
                {policies.map((p) => (
                  <tr key={p.id} className="hover:bg-[#151B28]/50 transition-colors">
                    <td className="p-3 font-mono font-bold text-[#635BFF]">{p.doc_id}</td>
                    <td className="p-3 font-medium text-[#F4F6FA]">{p.title}</td>
                    <td className="p-3 text-[#98A2B3]">{p.category}</td>
                    <td className="p-3 font-mono text-[#98A2B3]">v{p.version}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          p.status === 'ACTIVE'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-[#151B28] text-[#98A2B3] border-[#202838]'
                        }`}
                      >
                        {p.status}
                      </span>
                    </td>
                    <td className="p-3 text-[#98A2B3]">{p.effective_date}</td>
                    <td className="p-3 text-[#98A2B3] max-w-xs truncate">{p.source_reference}</td>
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

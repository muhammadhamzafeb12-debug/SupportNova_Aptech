import React, { useState, useEffect } from 'react';
import { Upload, Layers, FileText, CheckCircle2, AlertCircle, Eye, X, FileCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const KnowledgeBasePage = () => {
  const { token } = useAuth();
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('General');
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  
  const [statusMsg, setStatusMsg] = useState(null);
  const [selectedPolicyChunks, setSelectedPolicyChunks] = useState(null);

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/policies');
      if (res.ok) {
        setPolicies(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      if (!title) {
        const nameWithoutExt = droppedFile.name.replace(/\.[^/.]+$/, "");
        setTitle(nameWithoutExt);
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      if (!title) {
        const nameWithoutExt = selected.name.replace(/\.[^/.]+$/, "");
        setTitle(nameWithoutExt);
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setStatusMsg({ type: 'error', text: 'Please select or drag a PDF/DOCX/TXT file first.' });
      return;
    }
    
    try {
      setUploading(true);
      setStatusMsg(null);

      const formData = new FormData();
      formData.append('title', title || file.name);
      formData.append('category', category || 'General');
      formData.append('file', file);

      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch('/api/policies/upload', {
        method: 'POST',
        headers,
        body: formData
      });

      const data = await res.json();

      if (res.ok) {
        setStatusMsg({
          type: 'success',
          text: `Policy "${data.doc_id}" uploaded successfully & divided into ${data.chunk_count} traceable chunks!`
        });
        setTitle('');
        setCategory('General');
        setFile(null);
        await fetchPolicies();
      } else {
        setStatusMsg({
          type: 'error',
          text: data.detail || 'Failed to upload and chunk document.'
        });
      }
    } catch (err) {
      console.error(err);
      setStatusMsg({ type: 'error', text: 'Network error occurred while uploading document.' });
    } finally {
      setUploading(false);
    }
  };

  const viewChunks = async (policyId) => {
    try {
      const res = await fetch(`/api/policies/${policyId}/chunks`);
      if (res.ok) {
        const data = await res.json();
        setSelectedPolicyChunks(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
          AI Policy Base & Document Knowledge Engine
        </h1>
        <p className="text-xs lg:text-sm text-slate-400 mt-1">
          Active company policies, SOPs, and automated chunking repository ({policies.length} active policies).
        </p>
      </div>

      {/* Policy Precedence Bar */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-3.5 flex flex-wrap items-center justify-between text-xs text-slate-400 shadow-xl">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-400" />
          <span className="font-bold text-white">Policy Grounding Hierarchy:</span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="text-emerald-400 font-bold">ACTIVE POLICY</span> &gt;
          <span className="text-blue-400 font-bold">LATEST SOP</span> &gt;
          <span className="text-amber-400 font-bold">APPROVED FAQ</span>
        </div>
      </div>

      {/* Status Feedback Banner */}
      {statusMsg && (
        <div className={`p-4 rounded-xl border flex items-center justify-between ${
          statusMsg.type === 'success' 
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' 
            : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
        }`}>
          <div className="flex items-center gap-3 text-xs font-bold">
            {statusMsg.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
            )}
            <span>{statusMsg.text}</span>
          </div>
          <button onClick={() => setStatusMsg(null)} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Upload Panel */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 sm:p-6 space-y-4 shadow-xl">
        <h2 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
          <Upload className="w-4 h-4 text-blue-400" /> Upload Policy Document (PDF / DOCX / TXT)
        </h2>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-300 font-semibold block mb-1">Document Title</label>
              <input
                type="text"
                required
                placeholder="Return Inspection SOP 2026"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-300 font-semibold block mb-1">Category</label>
              <input
                type="text"
                required
                placeholder="Refund, Safety, Billing, Logistics"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer relative ${
              dragActive 
                ? 'border-blue-500 bg-blue-500/10' 
                : file 
                ? 'border-emerald-500/50 bg-emerald-500/5' 
                : 'border-slate-800 hover:border-blue-500/50 bg-slate-900/50'
            }`}
          >
            <input
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              onChange={handleFileChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            
            {file ? (
              <div className="flex items-center justify-center gap-3 text-emerald-400">
                <FileCheck className="w-8 h-8" />
                <div className="text-left">
                  <p className="text-xs font-bold text-white">{file.name}</p>
                  <p className="text-[11px] text-slate-400">{(file.size / 1024).toFixed(1)} KB — Ready to Chunk</p>
                </div>
              </div>
            ) : (
              <div className="space-y-1.5">
                <FileText className="w-8 h-8 text-blue-400 mx-auto" />
                <p className="text-xs text-white font-bold">
                  Drag and drop PDF / DOCX file here, or <span className="text-blue-400 underline">browse file</span>
                </p>
                <p className="text-[11px] text-slate-400">Automatic Document Chunking Engine</p>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={uploading || !file}
            className={`w-full py-2.5 font-bold rounded-lg text-xs transition-all flex items-center justify-center gap-2 ${
              uploading || !file
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/25'
            }`}
          >
            {uploading ? 'Chunking Document...' : 'Upload & Run Chunking Engine'}
          </button>
        </form>
      </div>

      {/* Policy Repository Table */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Policy Repository</h3>
          <span className="text-xs text-slate-400">Total: {policies.length}</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 font-medium">Loading policy documents...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-slate-900 text-slate-400 text-[11px] uppercase font-bold border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Doc ID</th>
                  <th className="p-3.5">Title</th>
                  <th className="p-3.5">Category</th>
                  <th className="p-3.5">Version</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {policies.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-900/60 transition-colors">
                    <td className="p-3.5 font-mono font-bold text-blue-400">{p.doc_id}</td>
                    <td className="p-3.5 font-bold text-white">{p.title}</td>
                    <td className="p-3.5 text-slate-300">{p.category}</td>
                    <td className="p-3.5 font-mono text-slate-400">v{p.version}</td>
                    <td className="p-3.5">
                      <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                        {p.status}
                      </span>
                    </td>
                    <td className="p-3.5 text-right">
                      <button
                        onClick={() => viewChunks(p.id)}
                        className="px-3 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-blue-400 font-bold rounded-lg flex items-center gap-1.5 ml-auto"
                      >
                        <Eye className="w-3.5 h-3.5" /> View Chunks
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Chunks Viewer Modal */}
      {selectedPolicyChunks && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-[#0D1322] border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">
                  Chunks Viewer: {selectedPolicyChunks.title} ({selectedPolicyChunks.doc_id})
                </h3>
                <p className="text-xs text-slate-400">
                  Extracted Traceable Chunks: {selectedPolicyChunks.total_chunks}
                </p>
              </div>
              <button
                onClick={() => setSelectedPolicyChunks(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto space-y-3 flex-1">
              {selectedPolicyChunks.chunks.map((c) => (
                <div key={c.id} className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-blue-400 font-bold">{c.section_id}</span>
                    <span className="text-slate-400 font-mono text-[11px]">Page {c.page_number} | v{c.version}</span>
                  </div>
                  <p className="text-xs font-bold text-white">{c.heading}</p>
                  <p className="text-xs text-slate-300 bg-[#060911] p-3 rounded-lg border border-slate-800 font-mono whitespace-pre-wrap">
                    {c.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

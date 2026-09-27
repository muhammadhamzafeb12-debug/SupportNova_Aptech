import React, { useState, useEffect, useRef } from 'react';
import {
  Upload, Layers, FileText, CheckCircle2, AlertCircle, Eye, X,
  FileCheck, Search, Brain, Database, Zap, ChevronRight, Cpu,
  BookOpen, Sparkles, ArrowRight, RefreshCw, MessageSquare, Star
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// ------- Animated RAG Pipeline Diagram -------
const RAGPipelineDiagram = ({ step }) => {
  const steps = [
    { id: 1, icon: FileText, label: 'Documents', sub: 'Upload & Parse', color: '#3b82f6' },
    { id: 2, icon: Cpu, label: 'Chunker', sub: 'Structure-Aware Split', color: '#8b5cf6' },
    { id: 3, icon: Database, label: 'Vector Store', sub: 'TF-IDF Index', color: '#06b6d4' },
    { id: 4, icon: Search, label: 'Similarity Search', sub: 'Cosine Score', color: '#f59e0b' },
    { id: 5, icon: Brain, label: 'LLM Engine', sub: 'Grounded Response', color: '#ef4444' },
    { id: 6, icon: MessageSquare, label: 'Response', sub: 'Cited Answer', color: '#10b981' },
  ];

  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-2 justify-center flex-wrap sm:flex-nowrap">
      {steps.map((s, i) => {
        const Icon = s.icon;
        const active = step >= s.id;
        const current = step === s.id;
        return (
          <React.Fragment key={s.id}>
            <div className={`flex flex-col items-center gap-1.5 transition-all duration-500 ${active ? 'opacity-100' : 'opacity-30'}`}>
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-500 ${
                  current ? 'ring-2 ring-offset-2 ring-offset-[#0D1322] scale-110' : ''
                }`}
                style={{ backgroundColor: active ? `${s.color}20` : '#1e293b', borderColor: active ? s.color : '#334155', border: '1px solid', ringColor: s.color }}
              >
                <Icon className="w-4 h-4" style={{ color: active ? s.color : '#475569' }} />
              </div>
              <div className="text-center">
                <p className="text-[10px] font-bold text-white whitespace-nowrap">{s.label}</p>
                <p className="text-[9px] text-slate-500 whitespace-nowrap">{s.sub}</p>
              </div>
            </div>
            {i < steps.length - 1 && (
              <ArrowRight className={`w-3.5 h-3.5 shrink-0 mb-4 transition-all duration-500 ${active && step > s.id ? 'text-blue-400' : 'text-slate-700'}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

// ------- Chunk Card -------
const ChunkCard = ({ chunk, index, delay }) => {
  return (
    <div
      className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2 hover:border-blue-500/30 transition-all animate-fade-in"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono font-bold text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded">{chunk.section_id}</span>
          <span className="text-[10px] text-slate-500">Page {chunk.page_number}</span>
        </div>
        <div className="flex items-center gap-1 bg-amber-500/10 border border-amber-500/20 rounded px-2 py-0.5">
          <Star className="w-2.5 h-2.5 text-amber-400" />
          <span className="text-[10px] font-bold text-amber-400">{(chunk.relevance_score * 100).toFixed(1)}%</span>
        </div>
      </div>
      <p className="text-xs font-bold text-white">{chunk.document_title}</p>
      <p className="text-[11px] text-slate-400 font-medium">{chunk.heading}</p>
      <p className="text-xs text-slate-300 bg-[#060911] p-3 rounded-lg border border-slate-800 font-mono whitespace-pre-wrap leading-relaxed">
        {chunk.content_snippet}
      </p>
    </div>
  );
};

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

  // RAG Query state
  const [ragQuery, setRagQuery] = useState('');
  const [ragTopK, setRagTopK] = useState(5);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragResult, setRagResult] = useState(null);
  const [ragStep, setRagStep] = useState(0);
  const ragResultRef = useRef(null);

  useEffect(() => { fetchPolicies(); }, []);

  const fetchPolicies = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/policies');
      if (res.ok) setPolicies(await res.json());
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleDrag = (e) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };
  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation(); setDragActive(false);
    if (e.dataTransfer.files?.[0]) {
      const f = e.dataTransfer.files[0];
      setFile(f);
      if (!title) setTitle(f.name.replace(/\.[^/.]+$/, ''));
    }
  };
  const handleFileChange = (e) => {
    if (e.target.files?.[0]) {
      const f = e.target.files[0];
      setFile(f);
      if (!title) setTitle(f.name.replace(/\.[^/.]+$/, ''));
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) { setStatusMsg({ type: 'error', text: 'Please select a PDF/DOCX/TXT file first.' }); return; }
    try {
      setUploading(true); setStatusMsg(null);
      const formData = new FormData();
      formData.append('title', title || file.name);
      formData.append('category', category || 'General');
      formData.append('file', file);
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch('/api/policies/upload', { method: 'POST', headers, body: formData });
      const data = await res.json().catch(() => ({ detail: 'Server error' }));
      if (res.ok) {
        setStatusMsg({ type: 'success', text: `✅ "${data.doc_id}" uploaded! Divided into ${data.chunk_count} traceable chunks & indexed in vector store.` });
        setTitle(''); setCategory('General'); setFile(null);
        await fetchPolicies();
      } else {
        setStatusMsg({ type: 'error', text: data.detail || 'Upload failed.' });
      }
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Backend unreachable. Make sure the backend is running on port 8000.' });
    } finally { setUploading(false); }
  };

  // RAG Query Handler
  const handleRAGQuery = async () => {
    if (!ragQuery.trim()) return;
    setRagLoading(true); setRagResult(null); setRagStep(1);

    const steps = [1, 2, 3, 4, 5, 6];
    let stepIndex = 0;
    const interval = setInterval(() => {
      stepIndex++;
      setRagStep(steps[stepIndex] ?? 6);
      if (stepIndex >= steps.length - 1) clearInterval(interval);
    }, 400);

    try {
      const res = await fetch('/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ query: ragQuery, top_k: ragTopK, min_score: 0.01 })
      });
      const data = await res.json();
      clearInterval(interval); setRagStep(6);
      setRagResult(data);
      setTimeout(() => ragResultRef.current?.scrollIntoView({ behavior: 'smooth' }), 200);
    } catch (err) {
      clearInterval(interval); setRagStep(0);
      setRagResult({ query: ragQuery, answer: 'Error connecting to backend.', sources: [], chunks_retrieved: 0 });
    } finally { setRagLoading(false); }
  };

  const viewChunks = async (policyId) => {
    try {
      const res = await fetch(`/api/policies/${policyId}/chunks`);
      if (res.ok) setSelectedPolicyChunks(await res.json());
    } catch (err) { console.error(err); }
  };

  const CATEGORY_OPTIONS = ['General', 'Refund', 'Billing', 'Safety', 'Delivery', 'Privacy', 'Warranty', 'Technical Support', 'Account', 'Product Defect', 'Escalation', 'SLA', 'Communication'];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
          AI Policy Base & RAG Query Engine
        </h1>
        <p className="text-xs lg:text-sm text-slate-400 mt-1">
          Upload company documents → auto-chunk → vector index → query with semantic similarity search → LLM grounded response.
        </p>
      </div>

      {/* Policy Precedence Bar */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-3 flex flex-wrap items-center justify-between text-xs text-slate-400 shadow-xl gap-3">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-400" />
          <span className="font-bold text-white">Policy Grounding Hierarchy:</span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="text-emerald-400 font-bold">ACTIVE POLICY</span> &gt;
          <span className="text-blue-400 font-bold">LATEST SOP</span> &gt;
          <span className="text-amber-400 font-bold">APPROVED FAQ</span>
        </div>
        <div className="text-[11px] text-slate-500">
          {policies.length} active documents · TF-IDF Vector Index
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
            {statusMsg.type === 'success'
              ? <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              : <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />}
            <span>{statusMsg.text}</span>
          </div>
          <button onClick={() => setStatusMsg(null)}><X className="w-4 h-4 text-slate-400 hover:text-white" /></button>
        </div>
      )}

      {/* ========= MAIN GRID: Upload + RAG Query ========= */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

        {/* ---- Upload Panel ---- */}
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <h2 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
            <Upload className="w-4 h-4 text-blue-400" /> Step 1: Upload Document (PDF / DOCX / TXT)
          </h2>
          <form onSubmit={handleUpload} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-300 font-semibold block mb-1">Document Title</label>
                <input
                  type="text" required placeholder="Return Policy 2026"
                  value={title} onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
              <div>
                <label className="text-xs text-slate-300 font-semibold block mb-1">Category</label>
                <select
                  value={category} onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 transition-colors"
                >
                  {CATEGORY_OPTIONS.map(opt => <option key={opt}>{opt}</option>)}
                </select>
              </div>
            </div>

            <div
              onDragEnter={handleDrag} onDragLeave={handleDrag}
              onDragOver={handleDrag} onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer relative ${
                dragActive ? 'border-blue-500 bg-blue-500/10'
                : file ? 'border-emerald-500/50 bg-emerald-500/5'
                : 'border-slate-700 hover:border-blue-500/50 bg-slate-900/50'
              }`}
            >
              <input type="file" accept=".pdf,.docx,.doc,.txt,.zip" onChange={handleFileChange} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
              {file ? (
                <div className="flex items-center justify-center gap-3 text-emerald-400">
                  <FileCheck className="w-8 h-8" />
                  <div className="text-left">
                    <p className="text-xs font-bold text-white">{file.name}</p>
                    <p className="text-[11px] text-slate-400">{(file.size / 1024).toFixed(1)} KB — Ready to chunk</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-1.5">
                  <FileText className="w-8 h-8 text-blue-400 mx-auto" />
                  <p className="text-xs text-white font-bold">Drag & drop PDF / DOCX / TXT here, or <span className="text-blue-400 underline">browse</span></p>
                  <p className="text-[11px] text-slate-500">Structure-aware chunking engine will auto-process your document</p>
                </div>
              )}
            </div>

            <button
              type="submit" disabled={uploading || !file}
              className={`w-full py-2.5 font-bold rounded-lg text-xs transition-all flex items-center justify-center gap-2 ${
                uploading || !file ? 'bg-slate-800 text-slate-500 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20'
              }`}
            >
              {uploading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Chunking & Indexing...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" /> Upload & Run Chunking Engine
                </>
              )}
            </button>
          </form>

          {/* Mini Chunking Steps */}
          <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-800">
            <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">What Happens After Upload:</p>
            <div className="space-y-1.5">
              {[
                { n: 1, t: 'Parse PDF/DOCX → extract raw text per page/paragraph' },
                { n: 2, t: 'Structure-aware chunker splits by sections (≤80 words, 20w overlap)' },
                { n: 3, t: 'Each chunk tagged with: Doc ID, Section ID, Heading, Page, Version' },
                { n: 4, t: 'TF-IDF Vector Index rebuilt — chunks immediately searchable' },
              ].map(item => (
                <div key={item.n} className="flex items-start gap-2">
                  <span className="text-[10px] font-bold text-blue-400 bg-blue-500/10 rounded-full w-4 h-4 flex items-center justify-center shrink-0 mt-0.5">{item.n}</span>
                  <p className="text-[11px] text-slate-400">{item.t}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ---- RAG Query Panel ---- */}
        <div className="bg-[#0D1322] border border-blue-500/20 rounded-xl p-5 space-y-4 shadow-xl shadow-blue-500/5">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <Brain className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-white">Step 2: RAG Query Engine</h2>
              <p className="text-[10px] text-slate-500">Semantic search → relevant chunks → LLM grounded answer</p>
            </div>
          </div>

          {/* Pipeline Diagram */}
          <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-800">
            <p className="text-[10px] font-bold text-slate-400 uppercase mb-3 text-center">RAG Pipeline Status</p>
            <RAGPipelineDiagram step={ragStep} />
          </div>

          {/* Search Input */}
          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-300 font-semibold block mb-1">Your Query / Question</label>
              <textarea
                rows={3}
                placeholder="e.g. What is the refund policy for damaged products? Or: How do I process a warranty claim?"
                value={ragQuery} onChange={(e) => setRagQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && e.ctrlKey) handleRAGQuery(); }}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500 transition-colors resize-none placeholder-slate-600"
              />
            </div>

            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400 font-semibold">Top-K chunks:</label>
                <select
                  value={ragTopK} onChange={(e) => setRagTopK(Number(e.target.value))}
                  className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  {[3, 5, 7, 10].map(k => <option key={k} value={k}>{k}</option>)}
                </select>
              </div>
              <button
                onClick={handleRAGQuery}
                disabled={ragLoading || !ragQuery.trim()}
                className={`flex items-center gap-2 px-5 py-2 font-bold rounded-lg text-xs transition-all ${
                  ragLoading || !ragQuery.trim()
                    ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/25'
                }`}
              >
                {ragLoading ? (
                  <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Searching...</>
                ) : (
                  <><Search className="w-3.5 h-3.5" /> Search & Ask LLM</>
                )}
              </button>
            </div>

            {/* Quick example queries */}
            <div className="flex flex-wrap gap-1.5">
              <p className="text-[10px] text-slate-500 font-semibold w-full">Quick Examples:</p>
              {[
                'What is the refund policy?',
                'How to handle a safety incident?',
                'Escalation rules for VIP customers',
                'GDPR data deletion request process',
              ].map(q => (
                <button
                  key={q} onClick={() => setRagQuery(q)}
                  className="text-[10px] px-2.5 py-1 rounded-full bg-slate-900 border border-slate-700 text-slate-400 hover:border-blue-500/50 hover:text-blue-400 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ========= RAG RESULTS ========= */}
      {ragResult && (
        <div ref={ragResultRef} className="space-y-4 animate-fade-in">
          {/* Query header */}
          <div className="bg-[#0D1322] border border-blue-500/30 rounded-xl p-5 shadow-xl shadow-blue-500/5">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">RAG Analysis Result</span>
                <span className="text-[10px] bg-blue-500/10 text-blue-400 font-bold px-2 py-0.5 rounded border border-blue-500/20">
                  {ragResult.chunks_retrieved} chunks retrieved
                </span>
              </div>
            </div>

            {/* Query echo */}
            <div className="flex items-start gap-3 mb-4">
              <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center shrink-0 mt-0.5">
                <Search className="w-3.5 h-3.5 text-slate-400" />
              </div>
              <div className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 flex-1">
                <p className="text-[10px] text-slate-500 font-bold mb-0.5">YOUR QUERY</p>
                <p className="text-sm text-white font-medium">{ragResult.query}</p>
              </div>
            </div>

            {/* LLM Answer */}
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-lg bg-blue-500/20 flex items-center justify-center shrink-0 mt-0.5">
                <Brain className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl px-4 py-3 flex-1">
                <p className="text-[10px] text-blue-400 font-bold mb-1">LLM GROUNDED RESPONSE (Pipeline 1)</p>
                <p className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">{ragResult.answer}</p>
              </div>
            </div>
          </div>

          {/* Retrieved Chunks */}
          {ragResult.sources?.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 px-1">
                <Database className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Retrieved Chunks ({ragResult.sources.length}) — Most Relevant First
                </h3>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {ragResult.sources.map((chunk, idx) => (
                  <ChunkCard key={idx} chunk={chunk} index={idx} delay={idx * 80} />
                ))}
              </div>
            </div>
          )}

          {ragResult.sources?.length === 0 && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-6 text-center">
              <AlertCircle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
              <p className="text-xs font-bold text-amber-400">No matching chunks found</p>
              <p className="text-[11px] text-slate-400 mt-1">Try uploading company policy documents first, or try a different query.</p>
            </div>
          )}
        </div>
      )}

      {/* ========= Policy Repository Table ========= */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-400" /> Policy Repository
          </h3>
          <span className="text-xs text-slate-400">{policies.length} total documents</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 font-medium">Loading policy documents...</div>
        ) : policies.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">No documents found. Upload your company policies above.</div>
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
                      <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-bold ${
                        p.status === 'ACTIVE'
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : 'bg-slate-700/50 text-slate-400 border border-slate-700'
                      }`}>{p.status}</span>
                    </td>
                    <td className="p-3.5 text-right">
                      <button
                        onClick={() => viewChunks(p.id)}
                        className="px-3 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-blue-400 font-bold rounded-lg flex items-center gap-1.5 ml-auto transition-colors"
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

      {/* ========= Chunks Viewer Modal ========= */}
      {selectedPolicyChunks && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-[#0D1322] border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[88vh] flex flex-col overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
              <div>
                <h3 className="text-sm font-bold text-white">
                  Chunks: {selectedPolicyChunks.title}
                  <span className="ml-2 font-mono text-xs text-blue-400">({selectedPolicyChunks.doc_id})</span>
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {selectedPolicyChunks.total_chunks} extractable chunks — ready for RAG retrieval
                </p>
              </div>
              <button onClick={() => setSelectedPolicyChunks(null)} className="text-slate-400 hover:text-white p-1 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto space-y-3 flex-1">
              {selectedPolicyChunks.chunks.map((c, idx) => (
                <div key={c.id} className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-2 hover:border-blue-500/20 transition-colors">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-blue-400 font-bold bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded">{c.section_id}</span>
                    <span className="text-slate-500 font-mono text-[10px]">Page {c.page_number} | v{c.version}</span>
                  </div>
                  <p className="text-xs font-bold text-white">{c.heading}</p>
                  <p className="text-xs text-slate-300 bg-[#060911] p-3 rounded-lg border border-slate-800 font-mono whitespace-pre-wrap leading-relaxed">
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

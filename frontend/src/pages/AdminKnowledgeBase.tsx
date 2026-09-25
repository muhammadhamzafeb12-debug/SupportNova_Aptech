import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { GlowButton } from '../components/GlowButton';
import { SkeletonLoader } from '../components/SkeletonLoader';
import {
  Upload, FileText, CheckCircle2, AlertTriangle, ShieldCheck,
  RefreshCw, ChevronDown, ChevronRight, X, Loader2, Clock, History,
  Play, Lock, User, AlertOctagon, Sparkles, ArrowRight
} from 'lucide-react';

interface KBDoc {
  id: number;
  document_id?: string;
  title: string;
  category: string;
  version: string;
  status: string;           // Active | Draft | Superseded | Previous
  effective_date: string;
  expiry_date?: string;
  file_name?: string;
  parsing_status?: string;   // pending | processing | completed | failed
  parsing_error?: string;
  chunk_count?: number;
  created_at?: string;
}

interface KBHistoryItem {
  document_id: string;
  title: string;
  category: string;
  version: string;
  status: string;
  effective_date: string;
  expiry_date?: string;
  is_expired?: boolean;
  created_at?: string;
  changed_by: string;
  changed_at: string;
  reason: string;
}

interface KBChunk {
  chunk_id: string;
  document_id: string;
  section: string;
  heading: string;
  page_reference: number;
  version: string;
  text: string;
  word_count: number;
}

const ParsingStatusBadge: React.FC<{ status?: string }> = ({ status }) => {
  switch (status) {
    case 'completed':
      return <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><CheckCircle2 className="w-3 h-3" /><span>Parsed</span></span>;
    case 'processing':
      return <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse"><Loader2 className="w-3 h-3 animate-spin" /><span>Processing</span></span>;
    case 'pending':
      return <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20"><Clock className="w-3 h-3" /><span>Pending</span></span>;
    case 'failed':
      return <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20"><AlertTriangle className="w-3 h-3" /><span>Failed</span></span>;
    default:
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-400">Unknown</span>;
  }
};

export const AdminKnowledgeBase: React.FC = () => {
  const [documents, setDocuments] = useState<KBDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('policy');
  const [version, setVersion] = useState('1.0');
  const [effectiveDate, setEffectiveDate] = useState(new Date().toISOString().split('T')[0]);
  const [expiryDate, setExpiryDate] = useState('');
  const [isDraft, setIsDraft] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [errorObj, setErrorObj] = useState<{ code: string; message: string } | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Chunk viewer state
  const [expandedChunkDocId, setExpandedChunkDocId] = useState<string | null>(null);
  const [chunks, setChunks] = useState<KBChunk[]>([]);
  const [chunksLoading, setChunksLoading] = useState(false);

  // History timeline modal state
  const [historyDoc, setHistoryDoc] = useState<KBDoc | null>(null);
  const [historyItems, setHistoryItems] = useState<KBHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Activate Draft modal state
  const [activateDoc, setActivateDoc] = useState<KBDoc | null>(null);
  const [activateReason, setActivateReason] = useState('');
  const [activating, setActivating] = useState(false);
  const [activateError, setActivateError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await api.listAdminKBDocuments();
      setDocuments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Poll status every 3s if any document is pending/processing
  useEffect(() => {
    const hasActiveProcessing = documents.some(
      d => d.parsing_status === 'pending' || d.parsing_status === 'processing'
    );
    if (!hasActiveProcessing) return;

    const interval = setInterval(async () => {
      try {
        const data = await api.listAdminKBDocuments();
        setDocuments(data);
      } catch {}
    }, 3000);

    return () => clearInterval(interval);
  }, [documents]);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    if (!title) setTitle(file.name.replace(/\.[^/.]+$/, "").replace(/_/g, " "));
    setErrorObj(null);
  };

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragOver(true); };
  const handleDragLeave = () => setIsDragOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setIsDragOver(false);
    if (e.dataTransfer.files?.[0]) handleFileSelect(e.dataTransfer.files[0]);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorObj(null); setSuccessMsg(null);
    if (!selectedFile) { setErrorObj({ code: 'missing_file', message: 'Please select or drag a file to upload.' }); return; }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('title', title);
    formData.append('category', category);
    formData.append('version', version);
    formData.append('effective_date', effectiveDate);
    if (expiryDate) formData.append('expiry_date', expiryDate);
    formData.append('is_draft', isDraft ? 'true' : 'false');

    try {
      const newDoc = await api.uploadKBDocument(formData);
      const docId = newDoc.document_id || `KB-DOC-${1000 + newDoc.id}`;
      setSuccessMsg(`Document '${newDoc.title}' uploaded as ${newDoc.status || 'Active'}! (ID: ${docId})`);
      setSelectedFile(null); setTitle(''); setVersion('1.0'); setExpiryDate(''); setIsDraft(false);
      fetchDocuments();
    } catch (err: any) {
      setErrorObj({ code: err.code || 'upload_failed', message: err.message || 'Upload failed.' });
    } finally {
      setUploading(false);
    }
  };

  const toggleChunks = async (docId: string) => {
    if (expandedChunkDocId === docId) {
      setExpandedChunkDocId(null);
      setChunks([]);
      return;
    }
    setExpandedChunkDocId(docId);
    setChunks([]);
    setChunksLoading(true);
    try {
      const resp = await api.getDocumentChunks(docId);
      setChunks(resp.chunks || []);
    } catch (err) {
      setChunks([]);
    } finally {
      setChunksLoading(false);
    }
  };

  const openHistory = async (doc: KBDoc) => {
    const docId = doc.document_id || `KB-DOC-${1000 + doc.id}`;
    setHistoryDoc(doc);
    setHistoryLoading(true);
    setHistoryItems([]);
    try {
      const resp = await api.getDocumentHistory(docId);
      setHistoryItems(resp.history || []);
    } catch (err) {
      setHistoryItems([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const openActivateModal = (doc: KBDoc) => {
    setActivateDoc(doc);
    setActivateReason('');
    setActivateError(null);
  };

  const handleActivateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activateDoc) return;
    const docId = activateDoc.document_id || `KB-DOC-${1000 + activateDoc.id}`;
    if (!activateReason.trim()) {
      setActivateError("Confirmation reason string is required to activate a draft policy.");
      return;
    }

    setActivating(true);
    setActivateError(null);
    try {
      await api.activateDocument(docId, activateReason.trim());
      setSuccessMsg(`Policy '${activateDoc.title}' (${docId}) has been promoted to Active status.`);
      setActivateDoc(null);
      fetchDocuments();
    } catch (err: any) {
      setActivateError(err.message || "Failed to activate policy.");
    } finally {
      setActivating(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-slide-up">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-6 rounded-2xl border border-dark-border">
        <div>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-brand-gradient flex items-center justify-center text-white shadow-glow-brand">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
                <span>Enterprise Policy Lifecycle & Audit Module</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/30">
                  Auditable Compliance
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Upload policies with SHA-256 deduplication, version superceding, draft promotion, and strict Active-only retrieval filtering.
              </p>
            </div>
          </div>
        </div>
        <button
          onClick={fetchDocuments}
          className="px-3.5 py-2 rounded-xl bg-dark-surface hover:bg-dark-surfaceHover border border-dark-border text-slate-300 hover:text-white transition flex items-center space-x-2 text-xs font-semibold"
          title="Refresh document repository"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-brand-400' : ''}`} />
          <span>Sync Repository</span>
        </button>
      </div>

      {/* Notifications */}
      {errorObj && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start space-x-3 shadow-glow-expired animate-fade-slide-up">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-rose-200 uppercase tracking-wider text-[10px]">Error Code: {errorObj.code}</div>
            <div className="mt-0.5">{errorObj.message}</div>
          </div>
          <button onClick={() => setErrorObj(null)} className="ml-auto text-rose-400 hover:text-rose-200"><X className="w-4 h-4" /></button>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center space-x-3 shadow-glow-active animate-fade-slide-up">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="ml-auto text-emerald-400 hover:text-emerald-200"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Upload Panel */}
      <div className="glass-card rounded-2xl p-6 border border-dark-border space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
            <Upload className="w-4 h-4 text-brand-400" />
            <span>Upload New Knowledge Document</span>
          </h2>
          <span className="text-[11px] text-slate-400">Max 20MB · PDF, DOCX, TXT, MD, CSV</span>
        </div>

        {/* Drag & Drop Area */}
        <div
          onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition cursor-pointer ${
            isDragOver ? 'border-brand-500 bg-brand-500/10 shadow-glow-brand' : selectedFile ? 'border-emerald-500/50 bg-emerald-500/5 shadow-glow-active' : 'border-dark-border hover:border-slate-700 bg-dark-bg/60'
          }`}
          onClick={() => document.getElementById('file-upload-input')?.click()}
        >
          <input id="file-upload-input" type="file" accept=".pdf,.docx,.txt,.md,.csv" className="hidden"
            onChange={e => { if (e.target.files?.[0]) handleFileSelect(e.target.files[0]); }} />
          <div className="w-12 h-12 rounded-xl bg-dark-surface border border-dark-border text-brand-400 flex items-center justify-center mx-auto mb-3 shadow-md">
            <Upload className="w-6 h-6" />
          </div>
          {selectedFile ? (
            <div>
              <span className="text-sm font-semibold text-emerald-400 block">{selectedFile.name}</span>
              <span className="text-xs text-slate-400">({(selectedFile.size / (1024*1024)).toFixed(2)} MB) — Ready for submission</span>
            </div>
          ) : (
            <div>
              <span className="text-sm font-semibold text-white block">Drag & drop policy document here, or click to browse</span>
              <span className="text-xs text-slate-500 mt-1 block">Supported: PDF, DOCX, TXT, MD, CSV (SHA-256 deduplication enforced)</span>
            </div>
          )}
        </div>

        <form onSubmit={handleUploadSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Document Title *</label>
            <input type="text" value={title} onChange={e => setTitle(e.target.value)} required placeholder="e.g. NexaLink Refund Policy 2026"
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Category *</label>
            <select value={category} onChange={e => setCategory(e.target.value)}
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
              <option value="policy">Policy</option>
              <option value="SOP">SOP</option>
              <option value="FAQ">FAQ</option>
              <option value="routing-rule">Routing Rule</option>
              <option value="escalation-rule">Escalation Rule</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Version Number *</label>
            <input type="text" value={version} onChange={e => setVersion(e.target.value)} required placeholder="e.g. 2.0"
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Effective Date *</label>
            <input type="date" value={effectiveDate} onChange={e => setEffectiveDate(e.target.value)} required
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Expiry Date (Optional)</label>
            <input type="date" value={expiryDate} onChange={e => setExpiryDate(e.target.value)}
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500" />
          </div>
          <div className="flex items-center space-x-2 pt-5">
            <label className="flex items-center space-x-2 cursor-pointer text-xs text-slate-300 font-semibold select-none">
              <input
                type="checkbox"
                checked={isDraft}
                onChange={e => setIsDraft(e.target.checked)}
                className="w-4 h-4 rounded bg-dark-bg border-dark-border text-brand-500 focus:ring-brand-500"
              />
              <span>Upload as Draft (Staging)</span>
            </label>
          </div>
          <div className="md:col-span-3 pt-2">
            <GlowButton type="submit" loading={uploading} icon={<Upload className="w-4 h-4" />} className="w-full">
              {uploading ? 'Processing & Vector Indexing...' : 'Upload & Process Policy Document'}
            </GlowButton>
          </div>
        </form>
      </div>

      {/* Document Registry Table */}
      <div className="glass-card rounded-2xl p-6 border border-dark-border space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Policy Registry & Version Status</h2>
          <span className="text-xs text-slate-400">{documents.length} Total Documents</span>
        </div>

        {loading ? (
          <SkeletonLoader rows={4} height="h-16" />
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">No knowledge documents found in repository.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-dark-border text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-3">Doc ID</th>
                  <th className="py-3 px-3">Title</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Version</th>
                  <th className="py-3 px-3">Lifecycle Status</th>
                  <th className="py-3 px-3">Parsing</th>
                  <th className="py-3 px-3">Chunks</th>
                  <th className="py-3 px-3">Effective</th>
                  <th className="py-3 px-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map(doc => {
                  const docId = doc.document_id || `KB-DOC-${1000 + doc.id}`;
                  const isExpanded = expandedChunkDocId === docId;
                  const isDraftDoc = (doc.status || '').toLowerCase() === 'draft';
                  const isExpiredDoc = checkIsExpired(doc.expiry_date);

                  return (
                    <React.Fragment key={docId}>
                      <tr className="border-b border-dark-border/60 hover:bg-dark-surface/50 transition">
                        <td className="py-3.5 px-3 font-mono text-brand-400 font-semibold">{docId}</td>
                        <td className="py-3.5 px-3 font-semibold text-white max-w-[220px] truncate">{doc.title}</td>
                        <td className="py-3.5 px-3 text-slate-300 capitalize">{doc.category}</td>
                        <td className="py-3.5 px-3 font-mono text-slate-300">v{doc.version || '1.0'}</td>
                        <td className="py-3.5 px-3">
                          <StatusBadge status={doc.status} type="document" isExpired={isExpiredDoc} />
                        </td>
                        <td className="py-3.5 px-3"><ParsingStatusBadge status={doc.parsing_status} /></td>
                        <td className="py-3.5 px-3 font-semibold text-slate-300">
                          {doc.parsing_status === 'completed' ? (
                            <span className="text-emerald-400 font-bold">{doc.chunk_count ?? 0}</span>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                        <td className="py-3.5 px-3 text-slate-400">{doc.effective_date || 'N/A'}</td>
                        <td className="py-3.5 px-3">
                          <div className="flex items-center space-x-2">
                            {/* Version History Button */}
                            <button
                              onClick={() => openHistory(doc)}
                              className="px-2.5 py-1 rounded-lg text-[11px] font-semibold text-slate-300 hover:text-white bg-dark-surface border border-dark-border hover:border-slate-600 transition flex items-center space-x-1"
                              title="View full audit history chain"
                            >
                              <History className="w-3 h-3 text-brand-400" />
                              <span>History</span>
                            </button>

                            {/* View Chunks Button */}
                            {doc.parsing_status === 'completed' && (
                              <button
                                onClick={() => toggleChunks(docId)}
                                className="px-2 py-1 rounded-lg text-[10px] font-semibold text-brand-400 hover:text-brand-300 bg-brand-500/10 border border-brand-500/20 transition flex items-center space-x-1"
                              >
                                {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                <span>Chunks</span>
                              </button>
                            )}

                            {/* Activate Button for Drafts */}
                            {isDraftDoc && (
                              <button
                                onClick={() => openActivateModal(doc)}
                                className="px-2 py-1 rounded-lg text-[10px] font-bold text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 border border-emerald-500/30 shadow-glow-active transition flex items-center space-x-1"
                              >
                                <Play className="w-3 h-3" />
                                <span>Activate</span>
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>

                      {/* Expandable Chunk Viewer */}
                      {isExpanded && (
                        <tr>
                          <td colSpan={9} className="bg-dark-bg/80 px-6 py-4 border-b border-dark-border">
                            {chunksLoading ? (
                              <div className="flex items-center space-x-2 text-xs text-slate-400">
                                <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
                                <span>Loading semantic chunks...</span>
                              </div>
                            ) : chunks.length === 0 ? (
                              <div className="text-xs text-slate-500">No chunks available for this document.</div>
                            ) : (
                              <div className="space-y-3">
                                <div className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">{chunks.length} Extracted Chunks</div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-80 overflow-y-auto pr-1">
                                  {chunks.map(c => (
                                    <div key={c.chunk_id} className="bg-dark-surface border border-dark-border rounded-xl p-3 space-y-1">
                                      <div className="flex items-center justify-between">
                                        <span className="text-[10px] font-bold text-brand-400 font-mono">{c.section}</span>
                                        <span className="text-[10px] text-slate-500">pg. {c.page_reference} · {c.word_count}w</span>
                                      </div>
                                      {c.heading && <div className="text-[11px] font-semibold text-white">{c.heading}</div>}
                                      <p className="text-[10px] text-slate-400 leading-relaxed line-clamp-3">{c.text}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Version History Timeline Modal ────────────────────────────────────── */}
      {historyDoc && (
        <div className="fixed inset-0 z-50 glass-modal flex items-center justify-center p-4">
          <div className="bg-dark-surface border border-dark-border rounded-2xl w-full max-w-2xl p-6 space-y-6 shadow-2xl animate-fade-slide-up">
            <div className="flex items-center justify-between pb-4 border-b border-dark-border">
              <div>
                <h3 className="text-base font-bold text-white flex items-center space-x-2">
                  <History className="w-5 h-5 text-brand-400" />
                  <span>Version History & Audit Trail</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">{historyDoc.title} ({historyDoc.category})</p>
              </div>
              <button onClick={() => setHistoryDoc(null)} className="text-slate-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            {historyLoading ? (
              <SkeletonLoader rows={3} height="h-16" />
            ) : historyItems.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">No version history records found.</div>
            ) : (
              <div className="relative pl-6 space-y-6 max-h-96 overflow-y-auto pr-2">
                {/* Vertical Timeline Bar */}
                <div className="absolute left-2.5 top-3 bottom-3 w-0.5 bg-gradient-to-b from-brand-500 via-brand-violet to-slate-800" />

                {historyItems.map((item, idx) => (
                  <div key={item.document_id + idx} className="relative timeline-item-stagger space-y-1">
                    {/* Glowing Node Circle */}
                    <div className={`absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 border-dark-surface ${
                      item.status === 'Active' ? 'bg-emerald-400 shadow-glow-active' :
                      item.status === 'Draft' ? 'bg-amber-400 shadow-glow-draft' : 'bg-slate-600'
                    }`} />

                    <div className="bg-dark-bg/80 border border-dark-border rounded-xl p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs font-bold text-brand-400">v{item.version}</span>
                          <StatusBadge status={item.status} type="document" isExpired={item.is_expired} />
                          <span className="font-mono text-[11px] text-slate-500">({item.document_id})</span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono">{formatDate(item.changed_at)}</span>
                      </div>

                      <div className="text-xs text-slate-300 flex items-center space-x-4">
                        <span className="flex items-center space-x-1 text-slate-400"><User className="w-3.5 h-3.5 text-brand-400" /><span>{item.changed_by}</span></span>
                        <span>·</span>
                        <span className="text-slate-400">Effective: <strong className="text-slate-200">{item.effective_date}</strong></span>
                        {item.expiry_date && <span>· Expiry: <strong className="text-rose-400">{item.expiry_date}</strong></span>}
                      </div>

                      {item.reason && (
                        <div className="text-[11px] text-slate-400 bg-dark-surface/60 rounded-lg p-2 border border-dark-border/50 italic">
                          "{item.reason}"
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-dark-border">
              <GlowButton variant="secondary" onClick={() => setHistoryDoc(null)}>Close</GlowButton>
            </div>
          </div>
        </div>
      )}

      {/* ── Activate Draft Confirmation Modal ─────────────────────────────────── */}
      {activateDoc && (
        <div className="fixed inset-0 z-50 glass-modal flex items-center justify-center p-4">
          <form onSubmit={handleActivateSubmit} className="bg-dark-surface border border-dark-border rounded-2xl w-full max-w-md p-6 space-y-5 shadow-2xl animate-fade-slide-up">
            <div className="flex items-center justify-between pb-3 border-b border-dark-border">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <span>Promote Policy to Active Status</span>
              </h3>
              <button type="button" onClick={() => setActivateDoc(null)} className="text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
            </div>

            <div className="text-xs text-slate-300 space-y-2">
              <p>You are activating policy document <strong className="text-white">{activateDoc.title}</strong> (v{activateDoc.version}).</p>
              <p className="text-amber-400 text-[11px]">
                ⚠️ Activating this policy will automatically supersede any existing Active policy of the same title & category.
              </p>
            </div>

            {activateError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 text-rose-400" />
                <span>{activateError}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Confirmation Reason *
              </label>
              <textarea
                value={activateReason}
                onChange={e => setActivateReason(e.target.value)}
                required
                rows={3}
                placeholder="Required: Type compliance or approval justification (e.g. Approved by Chief Compliance Officer)..."
                className="w-full bg-dark-bg border border-dark-border rounded-xl p-3 text-xs text-white focus:outline-none focus:border-brand-500"
              />
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <GlowButton type="button" variant="secondary" onClick={() => setActivateDoc(null)}>Cancel</GlowButton>
              <GlowButton type="submit" variant="success" loading={activating} icon={<CheckCircle2 className="w-4 h-4" />}>
                Confirm & Promote to Active
              </GlowButton>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

function checkIsExpired(expiryDateStr?: string): boolean {
  if (!expiryDateStr) return false;
  try {
    const exp = new Date(expiryDateStr);
    const now = new Date();
    return now > exp;
  } catch {
    return false;
  }
}

function formatDate(isoStr?: string): string {
  if (!isoStr) return '';
  try {
    return new Date(isoStr).toLocaleString();
  } catch {
    return isoStr;
  }
}

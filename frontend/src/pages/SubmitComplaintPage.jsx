import React, { useState } from 'react';
import { ShieldAlert, AlertTriangle, Send, Globe, Mail, MessageSquare, Upload, FileText, CheckCircle2 } from 'lucide-react';

export const SubmitComplaintPage = ({ onComplaintSubmitted }) => {
  const [channel, setChannel] = useState('WEB_FORM');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    customer_type: 'REGULAR',
    product_service: 'NovaCart Product Line',
    order_ref: '',
    transaction_ref: '',
    prev_complaint_ref: '',
    preferred_contact: 'EMAIL'
  });

  const [attachedFile, setAttachedFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [injectionDetected, setInjectionDetected] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    if (name === 'description' || name === 'title') {
      const lower = value.toLowerCase ? value.toLowerCase() : '';
      if (lower.includes('ignore') || lower.includes('prompt') || lower.includes('admin') || lower.includes('fake_policy')) {
        setInjectionDetected(true);
      } else {
        setInjectionDetected(false);
      }
    }
  };

  const handleFileUpload = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setAttachedFile(file);
      if (!formData.title) {
        const titleFromFilename = file.name.replace(/\.[^/.]+$/, "").replace(/_/g, " ");
        setFormData(prev => ({ ...prev, title: `Complaint via Document: ${titleFromFilename}` }));
      }

      if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          setFormData(prev => ({ ...prev, description: event.target.result }));
        };
        reader.readAsText(file);
      } else {
        setFormData(prev => ({
          ...prev,
          description: `[Attached Document: ${file.name} (${(file.size / 1024).toFixed(1)} KB)]\nPlease analyze the attached complaint document for product defect, billing refund, or delivery issues.`
        }));
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSubmitting(true);

    try {
      const payload = {
        ...formData,
        channel: channel
      };

      const res = await fetch('/api/complaints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Submission failed');
      }
      const created = await res.json();
      onComplaintSubmitted(created.id);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
          Submit Customer Complaint
        </h1>
        <p className="text-xs lg:text-sm text-slate-400 mt-1">
          Multi-channel complaint submission with real-time pre-processing, sanitization & prompt injection defense.
        </p>
      </div>

      {/* Multi-Channel Selector */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-3 grid grid-cols-2 sm:grid-cols-4 gap-2 shadow-xl">
        {[
          { id: 'WEB_FORM', label: 'Web Form', icon: Globe },
          { id: 'EMAIL', label: 'Email Intake', icon: Mail },
          { id: 'CHAT', label: 'Live Chat', icon: MessageSquare },
          { id: 'UPLOADED_COMPLAINT', label: 'Document Upload', icon: Upload }
        ].map((ch) => {
          const Icon = ch.icon;
          const isActive = channel === ch.id;
          return (
            <button
              key={ch.id}
              type="button"
              onClick={() => setChannel(ch.id)}
              className={`py-2.5 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 border transition-all ${
                isActive
                  ? 'bg-blue-600 text-white border-blue-500 shadow-md shadow-blue-500/20'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" /> {ch.label}
            </button>
          );
        })}
      </div>

      {/* Security Alert Banner */}
      {injectionDetected && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold">Prompt Injection Defense Active</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              The input text contains prompt manipulation keywords. SupportNova will isolate untrusted data and enforce strict Ground-Truth rule validation.
            </p>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Form Card */}
      <form onSubmit={handleSubmit} className="bg-[#0D1322] border border-slate-800 rounded-xl p-6 sm:p-8 space-y-4 shadow-xl">
        {channel === 'UPLOADED_COMPLAINT' && (
          <div className="border-2 border-dashed border-blue-500/40 bg-blue-500/5 rounded-xl p-6 text-center relative cursor-pointer hover:border-blue-500 transition-colors">
            <input
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              onChange={handleFileUpload}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            {attachedFile ? (
              <div className="flex items-center justify-center gap-2 text-emerald-400 text-xs font-bold">
                <CheckCircle2 className="w-5 h-5" />
                <span>Document Attached: {attachedFile.name} ({(attachedFile.size / 1024).toFixed(1)} KB)</span>
              </div>
            ) : (
              <div className="space-y-1.5">
                <FileText className="w-8 h-8 text-blue-400 mx-auto" />
                <p className="text-xs text-white font-bold">
                  Drop customer complaint PDF / DOCX file here, or <span className="text-blue-400 underline">click to browse</span>
                </p>
                <p className="text-[11px] text-slate-400">Supported formats: PDF, DOCX, TXT</p>
              </div>
            )}
          </div>
        )}

        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300">Complaint Title *</label>
          <input
            type="text"
            name="title"
            required
            placeholder="e.g. Overheating appliance caused kitchen smoke hazard"
            value={formData.title}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Customer Tier</label>
            <select
              name="customer_type"
              value={formData.customer_type}
              onChange={handleChange}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="REGULAR">Regular Customer</option>
              <option value="PREMIUM">Premium Account</option>
              <option value="VIP">VIP Client</option>
              <option value="CORPORATE">Corporate Enterprise</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Product / Service Affected</label>
            <input
              type="text"
              name="product_service"
              placeholder="NovaCart Appliance Line"
              value={formData.product_service}
              onChange={handleChange}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Order Reference</label>
            <input
              type="text"
              name="order_ref"
              placeholder="ORD-99821"
              value={formData.order_ref}
              onChange={handleChange}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Transaction Reference</label>
            <input
              type="text"
              name="transaction_ref"
              placeholder="TXN-44102"
              value={formData.transaction_ref}
              onChange={handleChange}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300">Detailed Complaint Description *</label>
          <textarea
            name="description"
            required
            rows="5"
            placeholder="Describe the complaint in detail (defect, billing issue, delivery delay, etc.)..."
            value={formData.description}
            onChange={handleChange}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          ></textarea>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/25"
        >
          <Send className="w-4 h-4" />
          <span>{submitting ? 'Submitting & Running Dual-Pipeline Analysis...' : 'Submit & Analyze Complaint'}</span>
        </button>
      </form>
    </div>
  );
};

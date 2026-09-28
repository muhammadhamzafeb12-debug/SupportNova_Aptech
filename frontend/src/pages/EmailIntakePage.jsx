import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Mail, Send, Paperclip, AlertTriangle, ShieldAlert,
  CheckCircle2, AtSign, User, FileText, Tag, MessageSquare, ChevronDown
} from 'lucide-react';

export const EmailIntakePage = ({ onComplaintSubmitted }) => {
  const { user, token } = useAuth();

  const [formData, setFormData] = useState({
    from_name: user?.full_name || '',
    from_email: user?.email || '',
    subject: '',
    customer_type: 'REGULAR',
    product_service: 'NovaCart Product Line',
    order_ref: '',
    transaction_ref: '',
    body: ''
  });

  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [injectionDetected, setInjectionDetected] = useState(false);
  const [sent, setSent] = useState(false);
  const [sentCode, setSentCode] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    if (name === 'subject' || name === 'body') {
      const lower = value.toLowerCase();
      setInjectionDetected(
        lower.includes('ignore') || lower.includes('prompt') ||
        lower.includes('admin') || lower.includes('fake_policy')
      );
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSubmitting(true);

    try {
      const title = formData.subject.trim() || `Email from ${formData.from_name}`;
      const description = `FROM: ${formData.from_name} <${formData.from_email}>\nTO: support@novacart.com\nSUBJECT: ${formData.subject}\n\n${formData.body}`;

      const payload = {
        title,
        description,
        customer_type: formData.customer_type,
        product_service: formData.product_service,
        order_ref: formData.order_ref,
        transaction_ref: formData.transaction_ref,
        channel: 'EMAIL',
        preferred_contact: 'EMAIL'
      };

      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/complaints', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Email submission failed');
      }

      const created = await res.json();
      setSentCode(created.complaint_code);
      setSent(true);

      // Navigate to detail after short delay
      setTimeout(() => {
        if (onComplaintSubmitted) onComplaintSubmitted(created.id);
      }, 2500);

    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (sent) {
    return (
      <div className="max-w-3xl mx-auto py-16 flex flex-col items-center justify-center gap-6 animate-fade-in">
        <div className="w-20 h-20 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shadow-2xl shadow-emerald-500/10">
          <CheckCircle2 className="w-10 h-10 text-emerald-400" />
        </div>
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-extrabold text-white">Email Complaint Sent!</h2>
          <p className="text-sm text-slate-400">
            Your complaint has been received and registered as ticket
          </p>
          <p className="text-lg font-mono font-bold text-blue-400 bg-blue-500/10 px-4 py-2 rounded-xl border border-blue-500/20 inline-block">
            {sentCode}
          </p>
          <p className="text-xs text-slate-500 mt-2">Redirecting to complaint detail...</p>
        </div>
        <div className="w-48 h-1 bg-slate-800 rounded-full overflow-hidden">
          <div className="h-full bg-blue-500 rounded-full animate-[width_2.5s_linear]" style={{ width: '100%', transition: 'width 2.5s linear' }}></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5 animate-fade-in">

      {/* Page Header */}
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
          <Mail className="w-7 h-7 text-blue-400" />
          Email Complaint Intake
        </h1>
        <p className="text-xs lg:text-sm text-slate-400 mt-1">
          Compose and submit your support complaint via email. Our system will analyze and route it automatically.
        </p>
      </div>

      {/* Prompt Injection Warning */}
      {injectionDetected && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold">Prompt Injection Defense Active</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Suspicious keywords detected. SupportNova will sanitize and enforce strict Ground-Truth validation.
            </p>
          </div>
        </div>
      )}

      {/* Error */}
      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Email Composer Card */}
      <form onSubmit={handleSend} className="bg-[#0D1322] border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">

        {/* Email Client Top Bar */}
        <div className="bg-slate-900/80 border-b border-slate-800 px-5 py-3 flex items-center gap-3">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500/70"></span>
            <span className="w-3 h-3 rounded-full bg-amber-500/70"></span>
            <span className="w-3 h-3 rounded-full bg-emerald-500/70"></span>
          </div>
          <span className="text-[11px] font-semibold text-slate-400 tracking-wide">New Complaint Email — SupportNova Mail Client</span>
        </div>

        {/* FROM Row */}
        <div className="flex items-center gap-3 px-5 py-3.5 border-b border-slate-800/70">
          <div className="flex items-center gap-2 w-20 shrink-0">
            <User className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">From</span>
          </div>
          <div className="flex-1 flex items-center gap-3">
            <input
              type="text"
              name="from_name"
              value={formData.from_name}
              onChange={handleChange}
              placeholder="Your Name"
              className="bg-transparent text-xs text-white placeholder-slate-600 focus:outline-none w-40"
            />
            <div className="flex items-center gap-1.5 bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[11px] font-mono px-2.5 py-1 rounded-full">
              <AtSign className="w-3 h-3" />
              <span>{formData.from_email || 'your@email.com'}</span>
            </div>
          </div>
          <span className="text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Authenticated</span>
        </div>

        {/* TO Row */}
        <div className="flex items-center gap-3 px-5 py-3.5 border-b border-slate-800/70">
          <div className="flex items-center gap-2 w-20 shrink-0">
            <Mail className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">To</span>
          </div>
          <div className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700 text-slate-300 text-[11px] font-mono px-2.5 py-1 rounded-full">
            <AtSign className="w-3 h-3 text-slate-400" />
            <span>support@novacart.com</span>
          </div>
          <span className="text-[10px] text-slate-500 ml-auto">SupportNova Complaint Desk</span>
        </div>

        {/* SUBJECT Row */}
        <div className="flex items-center gap-3 px-5 py-3.5 border-b border-slate-800/70">
          <div className="flex items-center gap-2 w-20 shrink-0">
            <Tag className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Subject</span>
          </div>
          <input
            type="text"
            name="subject"
            required
            value={formData.subject}
            onChange={handleChange}
            placeholder="e.g. Defective product received — Order ORD-12345"
            className="flex-1 bg-transparent text-sm font-semibold text-white placeholder-slate-600 focus:outline-none"
          />
        </div>

        {/* Extra Fields Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-0 border-b border-slate-800/70 divide-x divide-slate-800/70">
          <div className="px-5 py-3 space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Customer Tier</label>
            <div className="relative">
              <select
                name="customer_type"
                value={formData.customer_type}
                onChange={handleChange}
                className="w-full bg-transparent text-xs text-white focus:outline-none appearance-none cursor-pointer pr-5"
              >
                <option value="REGULAR" className="bg-slate-900">Regular Customer</option>
                <option value="PREMIUM" className="bg-slate-900">Premium Account</option>
                <option value="VIP" className="bg-slate-900">VIP Client</option>
                <option value="CORPORATE" className="bg-slate-900">Corporate Enterprise</option>
              </select>
              <ChevronDown className="w-3 h-3 text-slate-500 absolute right-0 top-0.5 pointer-events-none" />
            </div>
          </div>
          <div className="px-5 py-3 space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Order Ref</label>
            <input
              type="text"
              name="order_ref"
              value={formData.order_ref}
              onChange={handleChange}
              placeholder="ORD-12345"
              className="w-full bg-transparent text-xs text-white placeholder-slate-600 focus:outline-none"
            />
          </div>
          <div className="px-5 py-3 space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Transaction Ref</label>
            <input
              type="text"
              name="transaction_ref"
              value={formData.transaction_ref}
              onChange={handleChange}
              placeholder="TXN-44102"
              className="w-full bg-transparent text-xs text-white placeholder-slate-600 focus:outline-none"
            />
          </div>
        </div>

        {/* EMAIL BODY */}
        <div className="px-5 py-4 space-y-2">
          <textarea
            name="body"
            required
            rows="9"
            value={formData.body}
            onChange={handleChange}
            placeholder={`Dear Support Team,\n\nI am writing to report an issue with my recent order. [Describe your complaint in detail here — include the product, problem description, dates, and any relevant references.]\n\nThank you,\n${formData.from_name || 'Customer'}`}
            className="w-full bg-transparent text-xs text-white placeholder-slate-600 focus:outline-none resize-none leading-relaxed"
          />
        </div>

        {/* Footer Toolbar */}
        <div className="bg-slate-900/60 border-t border-slate-800 px-5 py-3.5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 text-slate-500">
            <button type="button" title="Attach file (not supported in demo)" className="p-1.5 hover:text-white transition-colors" disabled>
              <Paperclip className="w-4 h-4" />
            </button>
            <span className="text-[10px] font-mono">Channel: EMAIL · Dual-Pipeline AI Analysis Enabled</span>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl transition-all shadow-lg shadow-blue-500/25"
          >
            <Send className="w-4 h-4" />
            <span>{submitting ? 'Sending & Analyzing...' : 'Send Email & Submit Complaint'}</span>
          </button>
        </div>
      </form>

      {/* Info Note */}
      <div className="text-[11px] text-slate-500 flex items-center gap-2 px-1">
        <ShieldAlert className="w-3.5 h-3.5 text-blue-400 shrink-0" />
        Your email complaint will be processed by SupportNova's Dual-Pipeline AI engine (GenAI + Python Ground-Truth) for priority classification and routing.
      </div>
    </div>
  );
};

export default EmailIntakePage;

import React, { useState } from 'react';
import { ShieldAlert, AlertTriangle, Send } from 'lucide-react';

export const SubmitComplaintPage = ({ onComplaintSubmitted }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    customer_type: 'REGULAR',
    product_service: 'NovaCart Product Line',
    order_ref: '',
    transaction_ref: '',
    prev_complaint_ref: '',
    channel: 'WEB_FORM',
    preferred_contact: 'EMAIL'
  });
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSubmitting(true);

    try {
      const res = await fetch('/api/complaints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
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
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-[#202838]">
        <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
          Submit Customer Complaint
        </h1>
        <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
          File a complaint ticket for dual-pipeline AI & rule engine analysis
        </p>
      </div>

      {/* Security Alert Banner */}
      {injectionDetected && (
        <div className="p-3.5 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs flex items-start gap-3">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Prompt Injection Defense Triggered</div>
            <p className="text-[11px] text-[#98A2B3] mt-0.5">
              The text contains prompt manipulation keywords. SupportNova will enforce strict policy grounding and untrusted data isolation.
            </p>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="p-3 rounded-md bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Form Card */}
      <form onSubmit={handleSubmit} className="bg-[#101521] border border-[#202838] rounded-lg p-6 space-y-4">
        <div className="space-y-1">
          <label className="text-xs font-medium text-[#98A2B3]">Complaint Title *</label>
          <input
            type="text"
            name="title"
            required
            placeholder="e.g. Broken glass jug inside blender package"
            value={formData.title}
            onChange={handleChange}
            className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-[#98A2B3]">Customer Type</label>
            <select
              name="customer_type"
              value={formData.customer_type}
              onChange={handleChange}
              className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
            >
              <option value="REGULAR">Regular Customer</option>
              <option value="PREMIUM">Premium Customer</option>
              <option value="VIP">VIP Account</option>
              <option value="BUSINESS">Enterprise Client</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-[#98A2B3]">Product / Service</label>
            <input
              type="text"
              name="product_service"
              placeholder="NovaCart Kitchenware Series"
              value={formData.product_service}
              onChange={handleChange}
              className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-[#98A2B3]">Order Reference</label>
            <input
              type="text"
              name="order_ref"
              placeholder="ORD-99821"
              value={formData.order_ref}
              onChange={handleChange}
              className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-[#98A2B3]">Transaction Reference</label>
            <input
              type="text"
              name="transaction_ref"
              placeholder="TXN-44102"
              value={formData.transaction_ref}
              onChange={handleChange}
              className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
            />
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-[#98A2B3]">Detailed Complaint Description *</label>
          <textarea
            name="description"
            required
            rows="4"
            placeholder="Describe the complaint in detail..."
            value={formData.description}
            onChange={handleChange}
            className="w-full bg-[#151B28] border border-[#202838] rounded-md p-3 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
          ></textarea>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 px-4 bg-[#635BFF] hover:bg-[#5249E6] text-white font-medium text-xs rounded-md transition-colors flex items-center justify-center gap-2"
        >
          <Send className="w-4 h-4" />
          <span>{submitting ? 'Submitting & Processing...' : 'Submit Complaint'}</span>
        </button>
      </form>
    </div>
  );
};

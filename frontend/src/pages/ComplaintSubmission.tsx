import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { PlusCircle, CheckCircle2, ArrowRight } from 'lucide-react';

export const ComplaintSubmission: React.FC = () => {
  const navigate = useNavigate();
  const [customerEmail, setCustomerEmail] = useState('customer@nexalink.com');
  const [customerName, setCustomerName] = useState('Sarah Jenkins');
  const [accountNumber, setAccountNumber] = useState('ACC-994821');
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Billing Disputes & Overcharges');
  const [subCategory, setSubCategory] = useState('Roaming Fees');
  const [description, setDescription] = useState('');
  const [requestedCredit, setRequestedCredit] = useState<number>(0);

  const [submitting, setSubmitting] = useState(false);
  const [submittedCase, setSubmittedCase] = useState<any>(null);

  const categories = [
    'Billing Disputes & Overcharges',
    'Network Outages & Fiber Disconnection',
    'Hardware & Equipment Malfunction',
    'Service Cancellation & Retention',
    'Regulatory & FCC Complaints',
    'General Inquiry'
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const res = await api.createComplaint({
        customer_email: customerEmail,
        customer_name: customerName,
        account_number: accountNumber,
        title,
        category,
        sub_category: subCategory,
        description,
        requested_credit: Number(requestedCredit)
      });
      setSubmittedCase(res);
    } catch (err: any) {
      alert(err.message || 'Failed to submit complaint');
    } finally {
      setSubmitting(false);
    }
  };

  if (submittedCase) {
    return (
      <div className="max-w-xl mx-auto glass-card rounded-2xl p-8 border border-slate-800 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
          <CheckCircle2 className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold text-white">Complaint Submitted Successfully!</h2>
        <p className="text-xs text-slate-400">
          Your complaint reference number is <span className="font-mono font-bold text-brand-400">{submittedCase.complaint_number}</span>.
        </p>
        <div className="pt-4 flex justify-center space-x-3">
          <button
            onClick={() => {
              setSubmittedCase(null);
              setTitle('');
              setDescription('');
            }}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-4 py-2 rounded-xl text-xs"
          >
            Submit Another Complaint
          </button>
          <button
            onClick={() => navigate('/dashboard/customer')}
            className="bg-brand-600 hover:bg-brand-500 text-white font-semibold px-4 py-2 rounded-xl text-xs shadow-lg shadow-brand-500/20"
          >
            Go to My Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
          <PlusCircle className="w-5 h-5 text-brand-400" />
          <span>Submit Customer Complaint</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">Submit a new complaint for NexaLink dual-pipeline automated classification and resolution.</p>
      </div>

      <form onSubmit={handleSubmit} className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Customer Full Name *</label>
            <input
              type="text"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              required
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Customer Email *</label>
            <input
              type="email"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
              required
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Account Number</label>
            <input
              type="text"
              value={accountNumber}
              onChange={(e) => setAccountNumber(e.target.value)}
              placeholder="ACC-XXXXXX"
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Category *</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Complaint Title *</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            placeholder="Brief summary of the issue..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Detailed Description *</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            rows={4}
            placeholder="Provide all relevant details regarding downtime, unexpected fees, or service failure..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-brand-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Requested Credit Amount ($)</label>
          <input
            type="number"
            value={requestedCredit}
            onChange={(e) => setRequestedCredit(Number(e.target.value))}
            placeholder="0.00"
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-semibold py-2.5 rounded-xl text-xs transition shadow-lg shadow-brand-500/20 flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          <span>{submitting ? 'Submitting Complaint...' : 'Submit Complaint'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};

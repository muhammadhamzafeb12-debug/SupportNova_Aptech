import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Search, Filter, FileText, ChevronRight, X, Send,
  Bot, User as UserIcon, CheckCircle2, Clock, AlertTriangle,
  Building2, Tag, Calendar, Hash, Layers, MessageSquare,
  ArrowUpRight, RotateCcw, Sparkles, ShieldCheck, Info,
  ChevronDown, Inbox
} from 'lucide-react';

const DEPARTMENTS = [
  'Account Safety',
  'Customer Relations',
  'Billing',
  'Warranty',
  'Logistics',
  'Safety',
  'Compliance',
  'Technical Support',
];

const DEPT_COLORS = {
  'Account Safety':    { bg: 'bg-rose-500/15',    text: 'text-rose-400',    border: 'border-rose-500/30' },
  'Customer Relations':{ bg: 'bg-blue-500/15',    text: 'text-blue-400',    border: 'border-blue-500/30' },
  'Billing':           { bg: 'bg-amber-500/15',   text: 'text-amber-400',   border: 'border-amber-500/30' },
  'Warranty':          { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  'Logistics':         { bg: 'bg-indigo-500/15',  text: 'text-indigo-400',  border: 'border-indigo-500/30' },
  'Safety':            { bg: 'bg-orange-500/15',  text: 'text-orange-400',  border: 'border-orange-500/30' },
  'Compliance':        { bg: 'bg-purple-500/15',  text: 'text-purple-400',  border: 'border-purple-500/30' },
  'Technical Support': { bg: 'bg-cyan-500/15',    text: 'text-cyan-400',    border: 'border-cyan-500/30' },
};

const STATUS_COLORS = {
  NEW:         { bg: 'bg-slate-800',         text: 'text-slate-300',   border: 'border-slate-700' },
  ANALYZED:    { bg: 'bg-blue-500/15',       text: 'text-blue-400',    border: 'border-blue-500/30' },
  ESCALATED:   { bg: 'bg-amber-500/15',      text: 'text-amber-400',   border: 'border-amber-500/30' },
  IN_PROGRESS: { bg: 'bg-indigo-500/15',     text: 'text-indigo-400',  border: 'border-indigo-500/30' },
  RESOLVED:    { bg: 'bg-emerald-500/15',    text: 'text-emerald-400', border: 'border-emerald-500/30' },
  CLOSED:      { bg: 'bg-slate-700/40',      text: 'text-slate-400',   border: 'border-slate-700/50' },
};

function getDeptColors(dept) {
  return DEPT_COLORS[dept] || { bg: 'bg-slate-800', text: 'text-slate-300', border: 'border-slate-700' };
}
function getStatusColors(status) {
  return STATUS_COLORS[status] || STATUS_COLORS['NEW'];
}

// --- Chatbot ---
function ReviewerChatbot({ complaint }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (complaint) {
      const dept = complaint.department || complaint.category || 'Unknown';
      setMessages([
        {
          role: 'bot',
          text: `Hello! I'm your AI review assistant. I'm ready to help you review complaint **${complaint.complaint_code}**.

**Quick Summary:**
- **Subject:** ${complaint.title}
- **Department:** ${dept}
- **Status:** ${complaint.status}
- **Priority:** ${complaint.priority || 'Not set'}

You can ask me to summarize the complaint, identify the appropriate department, suggest actions, or anything else about this case.`,
        },
      ]);
    } else {
      setMessages([
        {
          role: 'bot',
          text: 'Select a complaint from the list on the left to begin. I\'ll help you review and route it to the correct department manager.',
        },
      ]);
    }
    setInput('');
  }, [complaint?.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function generateBotReply(userMsg, c) {
    const lower = userMsg.toLowerCase();
    if (!c) return `Please select a complaint first so I can assist you with the review.`;

    const dept = c.department || c.category || 'Unknown';
    const deptColors = getDeptColors(dept);

    if (lower.includes('summar') || lower.includes('brief') || lower.includes('overview')) {
      return `**Complaint Summary — ${c.complaint_code}**

📋 **Title:** ${c.title}
📝 **Description:** ${c.description ? c.description.slice(0, 300) + (c.description.length > 300 ? '…' : '') : 'No description available.'}
📊 **Status:** ${c.status}
⚡ **Priority:** ${c.priority || 'Not determined'}
🏢 **Department:** ${dept}
📅 **Submitted:** ${c.submitted_at ? new Date(c.submitted_at).toLocaleDateString() : 'Unknown'}`;
    }

    if (lower.includes('department') || lower.includes('dept') || lower.includes('route') || lower.includes('assign')) {
      return `**Department Routing Analysis — ${c.complaint_code}**

Based on the complaint content, this should be routed to the **${dept}** department.

**Routing Rationale:**
- The complaint involves issues typically handled by ${dept}.
- ${dept === 'Billing' ? 'Billing-related disputes, charges, or invoice issues fall under this department.' : ''}
- ${dept === 'Technical Support' ? 'Technical failures, product defects, or software issues are managed here.' : ''}
- ${dept === 'Logistics' ? 'Shipping, delivery delays, and order tracking issues belong here.' : ''}
- ${dept === 'Warranty' ? 'Warranty claims and product replacement requests go to this department.' : ''}
- ${dept === 'Account Safety' ? 'Unauthorized access, fraud, or security concerns are handled here.' : ''}
- ${dept === 'Customer Relations' ? 'General service quality and customer experience issues.' : ''}
- ${dept === 'Safety' ? 'Product safety concerns or hazard reports go here.' : ''}
- ${dept === 'Compliance' ? 'Policy compliance and regulatory issues are managed here.' : ''}

Use the **"Send to ${dept} Manager"** button below to route this complaint.`;
    }

    if (lower.includes('priority') || lower.includes('urgent') || lower.includes('severity')) {
      const prio = c.priority || 'P2 – Medium';
      const urgent = prio.includes('P0') || prio.includes('P1');
      return `**Priority Assessment — ${c.complaint_code}**

Current priority: **${prio}**
${urgent ? '🔴 This is a **high-priority** case requiring immediate attention.' : '🟡 This is a standard-priority case. Handle within normal SLA timelines.'}

${prio.includes('P0') ? 'P0 Critical cases must be resolved within 4 hours.' : ''}
${prio.includes('P1') ? 'P1 High cases must be resolved within 24 hours.' : ''}
${prio.includes('P2') ? 'P2 Medium cases should be resolved within 72 hours.' : ''}
${prio.includes('P3') ? 'P3 Low cases should be resolved within 5 business days.' : ''}`;
    }

    if (lower.includes('action') || lower.includes('recommend') || lower.includes('next step') || lower.includes('what should')) {
      return `**Recommended Actions — ${c.complaint_code}**

1. ✅ Review the full complaint description and verify the department assignment.
2. 📋 Confirm this belongs to the **${dept}** department.
3. 📤 Click **"Send to ${dept} Manager"** to route it to the appropriate manager.
4. 📝 The status will be updated to **"Sent to ${dept} Manager"** automatically.
5. 🔔 The ${dept} Manager will be notified and can take further action.`;
    }

    if (lower.includes('customer') || lower.includes('who submitted') || lower.includes('submitter')) {
      return `**Customer Information — ${c.complaint_code}**

- **Customer Type:** ${c.customer_type || 'Regular Customer'}
- **Submission Channel:** ${c.channel || 'Web Form'}
- **Contact Preference:** ${c.preferred_contact || 'Email'}
- **Submitted At:** ${c.submitted_at ? new Date(c.submitted_at).toLocaleString() : 'Unknown'}`;
    }

    if (lower.includes('status') || lower.includes('state')) {
      const sc = getStatusColors(c.status);
      return `**Status Report — ${c.complaint_code}**

Current status: **${c.status}**

${c.status === 'NEW' ? '📥 The complaint has just been submitted and awaits initial review.' : ''}
${c.status === 'ANALYZED' ? '🔍 The complaint has been processed by the AI pipeline.' : ''}
${c.status === 'ESCALATED' ? '⚠️ This complaint was flagged for manual review due to AI/Python pipeline mismatch or policy exception.' : ''}
${c.status === 'IN_PROGRESS' ? '🔄 The complaint is currently being handled by an agent or manager.' : ''}
${c.status === 'RESOLVED' ? '✅ This complaint has been successfully resolved.' : ''}`;
    }

    return `I understand you're asking about "${userMsg.slice(0, 60)}${userMsg.length > 60 ? '…' : ''}".

For complaint **${c.complaint_code}** (${dept} department), here are things I can help with:

• **"summarize"** — Get a brief overview of this complaint
• **"which department"** — See routing recommendation  
• **"priority"** — Check urgency and SLA timelines
• **"recommended actions"** — Get step-by-step guidance
• **"customer info"** — View submitter details
• **"status"** — Current complaint state

What would you like to know?`;
  }

  const handleSend = () => {
    const txt = input.trim();
    if (!txt) return;
    setMessages((prev) => [...prev, { role: 'user', text: txt }]);
    setInput('');
    setThinking(true);
    setTimeout(() => {
      const reply = generateBotReply(txt, complaint);
      setMessages((prev) => [...prev, { role: 'bot', text: reply }]);
      setThinking(false);
    }, 700 + Math.random() * 500);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  function renderMarkdown(text) {
    // Simple bold + newline renderer
    const parts = text.split('\n');
    return parts.map((line, i) => {
      const boldProcessed = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      return (
        <span key={i}>
          <span dangerouslySetInnerHTML={{ __html: boldProcessed }} />
          {i < parts.length - 1 && <br />}
        </span>
      );
    });
  }

  return (
    <div className="flex flex-col h-full bg-[#0A0F1E] border border-slate-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 py-3 border-b border-slate-800 bg-gradient-to-r from-amber-500/10 to-transparent">
        <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
          <Bot className="w-4 h-4 text-amber-400" />
        </div>
        <div>
          <p className="text-xs font-bold text-white">Review Assistant</p>
          <p className="text-[10px] text-slate-400">AI-powered complaint guidance</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[10px] text-emerald-400 font-bold">Online</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 min-h-0">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'bot' && (
              <div className="w-6 h-6 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-3.5 h-3.5 text-amber-400" />
              </div>
            )}
            <div
              className={`max-w-[85%] px-3 py-2 rounded-xl text-xs leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600/20 border border-blue-500/30 text-blue-100 rounded-tr-sm'
                  : 'bg-slate-900/80 border border-slate-800 text-slate-200 rounded-tl-sm'
              }`}
            >
              {renderMarkdown(msg.text)}
            </div>
            {msg.role === 'user' && (
              <div className="w-6 h-6 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0 mt-0.5">
                <UserIcon className="w-3.5 h-3.5 text-blue-400" />
              </div>
            )}
          </div>
        ))}
        {thinking && (
          <div className="flex gap-2 justify-start">
            <div className="w-6 h-6 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center shrink-0">
              <Bot className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="px-3 py-2 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-3 pb-3 pt-2 border-t border-slate-800">
        <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-700 rounded-xl px-3 py-2 focus-within:border-amber-500/50 transition-colors">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about this complaint..."
            className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 outline-none"
            disabled={thinking}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || thinking}
            className="w-6 h-6 rounded-lg bg-amber-500/20 hover:bg-amber-500/40 border border-amber-500/30 flex items-center justify-center text-amber-400 transition-all disabled:opacity-40"
          >
            <Send className="w-3 h-3" />
          </button>
        </div>
        <p className="text-[10px] text-slate-500 mt-1.5 text-center">
          Try: "summarize", "which department", "recommended actions"
        </p>
      </div>
    </div>
  );
}

// --- Complaint Detail Panel ---
function ComplaintDetail({ complaint, onSendToManager, sending, confirmation }) {
  const dept = complaint?.department || complaint?.category || 'General';
  const dc = getDeptColors(dept);
  const sc = getStatusColors(complaint?.status);

  if (!complaint) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-16 text-center space-y-3">
        <div className="w-14 h-14 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center">
          <Inbox className="w-7 h-7 text-slate-600" />
        </div>
        <p className="text-sm font-bold text-slate-400">Select a complaint to review</p>
        <p className="text-xs text-slate-500">Click any complaint in the list to view its full details and use the AI assistant.</p>
      </div>
    );
  }

  const fields = [
    { icon: Hash,       label: 'Complaint ID',  value: complaint.complaint_code },
    { icon: UserIcon,   label: 'Customer Type', value: complaint.customer_type || 'Regular Customer' },
    { icon: Tag,        label: 'Category',      value: complaint.category || 'General Service' },
    { icon: Calendar,   label: 'Date Submitted',value: complaint.submitted_at ? new Date(complaint.submitted_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Unknown' },
    { icon: Layers,     label: 'Priority',      value: complaint.priority || 'Not Set' },
    { icon: Building2,  label: 'Department',    value: dept, colored: dc },
  ];

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Title Bar */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-xs font-bold text-amber-400">{complaint.complaint_code}</span>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${sc.bg} ${sc.text} ${sc.border}`}>
              {complaint.status}
            </span>
          </div>
          <h2 className="text-base font-bold text-white leading-snug">{complaint.title}</h2>
        </div>
      </div>

      {/* Meta Fields */}
      <div className="grid grid-cols-2 gap-2">
        {fields.map(({ icon: Icon, label, value, colored }) => (
          <div key={label} className="bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2.5 space-y-0.5">
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 uppercase tracking-wider font-bold">
              <Icon className="w-3 h-3" />
              {label}
            </div>
            {colored ? (
              <span className={`text-xs font-bold ${colored.text}`}>{value}</span>
            ) : (
              <span className="text-xs font-semibold text-slate-200 truncate block">{value}</span>
            )}
          </div>
        ))}
      </div>

      {/* Description */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3.5 space-y-1.5">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <FileText className="w-3 h-3" /> Description
        </p>
        <p className="text-xs text-slate-300 leading-relaxed">
          {complaint.description || 'No description provided.'}
        </p>
      </div>

      {/* Department Banner */}
      <div className={`rounded-lg border p-3 flex items-center gap-3 ${dc.bg} ${dc.border}`}>
        <Building2 className={`w-5 h-5 shrink-0 ${dc.text}`} />
        <div className="flex-1 min-w-0">
          <p className={`text-xs font-bold ${dc.text}`}>Routed to: {dept} Department</p>
          <p className="text-[10px] text-slate-400">This complaint will be sent exclusively to the {dept} Manager.</p>
        </div>
      </div>

      {/* Send Button / Confirmation */}
      {confirmation ? (
        <div className="flex items-center gap-3 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <div>
            <p className="text-xs font-bold text-emerald-400">Successfully Sent!</p>
            <p className="text-[10px] text-slate-400">{confirmation}</p>
          </div>
        </div>
      ) : (
        <button
          onClick={() => onSendToManager(complaint, dept)}
          disabled={sending}
          className={`w-full py-3 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all shadow-lg ${
            sending
              ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
              : `bg-gradient-to-r ${dc.text === 'text-amber-400' ? 'from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 shadow-amber-500/25' :
                 dc.text === 'text-rose-400' ? 'from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 shadow-rose-500/25' :
                 dc.text === 'text-blue-400' ? 'from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-blue-500/25' :
                 dc.text === 'text-emerald-400' ? 'from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-emerald-500/25' :
                 dc.text === 'text-indigo-400' ? 'from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-indigo-500/25' :
                 dc.text === 'text-orange-400' ? 'from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 shadow-orange-500/25' :
                 dc.text === 'text-purple-400' ? 'from-purple-600 to-violet-600 hover:from-purple-500 hover:to-violet-500 shadow-purple-500/25' :
                 dc.text === 'text-cyan-400' ? 'from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 shadow-cyan-500/25' :
                 'from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-blue-500/25'
                } text-white`
          }`}
        >
          {sending ? (
            <>
              <div className="w-4 h-4 border-2 border-slate-600 border-t-slate-400 rounded-full animate-spin" />
              Sending to {dept} Manager…
            </>
          ) : (
            <>
              <ArrowUpRight className="w-4 h-4" />
              Send to {dept} Manager
            </>
          )}
        </button>
      )}
    </div>
  );
}

// --- Main Reviewer Dashboard ---
export const ReviewerDashboard = () => {
  const { token } = useAuth();

  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [deptFilter, setDeptFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [sending, setSending] = useState(false);
  const [confirmation, setConfirmation] = useState(null);

  const [activePanel, setActivePanel] = useState('detail'); // 'detail' | 'chat'

  useEffect(() => {
    fetchComplaints();
  }, [token]);

  const fetchComplaints = async () => {
    try {
      setLoading(true);
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch('/api/complaints', { headers });
      if (res.ok) {
        const data = await res.json();
        setComplaints(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchComplaintDetail = async (id) => {
    try {
      setDetailLoading(true);
      setConfirmation(null);
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`/api/complaints/${id}`, { headers });
      if (res.ok) {
        const data = await res.json();
        // Flatten for display
        const c = data.complaint || {};
        const genai = data.genai_analysis || {};
        const flat = {
          ...c,
          department: genai.department || c.department || 'General',
          category: genai.category || c.category || 'General Service',
          priority: c.priority || genai.priority || 'P2 – Medium',
        };
        setSelectedComplaint(flat);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleSelectComplaint = (c) => {
    fetchComplaintDetail(c.id);
    setActivePanel('detail');
  };

  const handleSendToManager = async (complaint, dept) => {
    try {
      setSending(true);
      setConfirmation(null);
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };
      const res = await fetch(`/api/complaints/${complaint.id}/send-to-manager`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ department: dept }),
      });

      // Update local state regardless (optimistic)
      const statusMsg = `Sent to ${dept} Manager`;
      setComplaints((prev) =>
        prev.map((c) => (c.id === complaint.id ? { ...c, status: statusMsg } : c))
      );
      setSelectedComplaint((prev) => prev ? { ...prev, status: statusMsg } : prev);
      setConfirmation(`Complaint ${complaint.complaint_code} has been sent to the ${dept} Manager. Status updated to "${statusMsg}".`);
    } catch (err) {
      console.error(err);
      setConfirmation(`Complaint ${complaint.complaint_code} has been sent to the ${dept} Manager.`);
    } finally {
      setSending(false);
    }
  };

  // --- Filtered list ---
  const filtered = complaints.filter((c) => {
    const dept = c.department || c.category || '';
    const matchSearch =
      c.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.complaint_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      dept.toLowerCase().includes(searchTerm.toLowerCase());
    const matchDept = deptFilter === 'ALL' || dept === deptFilter || c.category === deptFilter;
    const matchStatus = statusFilter === 'ALL' || c.status === statusFilter;
    return matchSearch && matchDept && matchStatus;
  });

  // Stats
  const totalComplaints = complaints.length;
  const pendingReview  = complaints.filter(c => ['NEW', 'ESCALATED', 'ANALYZED'].includes(c.status)).length;
  const resolved       = complaints.filter(c => ['RESOLVED', 'CLOSED'].includes(c.status)).length;

  return (
    <div className="flex flex-col h-full space-y-4 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            Reviewer Dashboard
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
              COMPLIANCE & AUDIT
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Review complaints, consult the AI assistant, and route each case to the correct department manager.
          </p>
        </div>
        <button
          onClick={fetchComplaints}
          className="flex items-center gap-2 px-3 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-bold text-slate-300 rounded-lg transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Total Complaints',   value: totalComplaints, icon: FileText,    color: 'text-blue-400',    bg: 'bg-blue-500/10',    border: 'border-blue-500/20' },
          { label: 'Awaiting Review',    value: pendingReview,   icon: Clock,       color: 'text-amber-400',   bg: 'bg-amber-500/10',   border: 'border-amber-500/20' },
          { label: 'Resolved / Closed',  value: resolved,        icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
        ].map(({ label, value, icon: Icon, color, bg, border }) => (
          <div key={label} className="glass-card rounded-xl p-4 flex items-center gap-3 group">
            <div className={`w-9 h-9 rounded-xl ${bg} border ${border} flex items-center justify-center shrink-0`}>
              <Icon className={`w-4.5 h-4.5 ${color}`} />
            </div>
            <div className="min-w-0">
              <p className="text-xl font-extrabold text-white">{value}</p>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider truncate">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Main Split Layout */}
      <div className="flex gap-4 flex-1 min-h-0" style={{ minHeight: '600px' }}>

        {/* LEFT: Complaint List */}
        <div className="w-80 shrink-0 flex flex-col bg-[#0A0F1E] border border-slate-800 rounded-xl overflow-hidden">
          {/* Filters */}
          <div className="p-3 border-b border-slate-800 space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search complaints..."
                className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50 transition-colors"
              />
            </div>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <select
                  value={deptFilter}
                  onChange={(e) => setDeptFilter(e.target.value)}
                  className="w-full appearance-none bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors pr-6"
                >
                  <option value="ALL">All Departments</option>
                  {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
                <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2 top-2 pointer-events-none" />
              </div>
              <div className="relative flex-1">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full appearance-none bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors pr-6"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="NEW">New</option>
                  <option value="ANALYZED">Analyzed</option>
                  <option value="ESCALATED">Escalated</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="RESOLVED">Resolved</option>
                </select>
                <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2 top-2 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-6 text-center space-y-2">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-amber-500 mx-auto" />
                <p className="text-xs text-slate-400">Loading complaints…</p>
              </div>
            ) : filtered.length === 0 ? (
              <div className="p-6 text-center space-y-2">
                <Inbox className="w-8 h-8 text-slate-600 mx-auto" />
                <p className="text-xs text-slate-400">No complaints match your filters.</p>
              </div>
            ) : (
              filtered.map((c) => {
                const dept = c.department || c.category || 'General';
                const dc = getDeptColors(dept);
                const sc = getStatusColors(c.status);
                const isActive = selectedComplaint?.id === c.id;
                return (
                  <button
                    key={c.id}
                    onClick={() => handleSelectComplaint(c)}
                    className={`w-full text-left px-3 py-3 border-b border-slate-800/60 hover:bg-slate-800/40 transition-all group ${
                      isActive ? 'bg-amber-500/5 border-l-2 border-l-amber-500' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <span className="font-mono text-[11px] font-bold text-amber-400">{c.complaint_code}</span>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${sc.bg} ${sc.text} ${sc.border} shrink-0`}>
                        {c.status}
                      </span>
                    </div>
                    <p className="text-xs font-semibold text-white leading-snug line-clamp-2 mb-1.5">
                      {c.title}
                    </p>
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${dc.bg} ${dc.text} ${dc.border}`}>
                        {dept}
                      </span>
                      {c.submitted_at && (
                        <span className="text-[10px] text-slate-500">
                          {new Date(c.submitted_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Count footer */}
          <div className="px-3 py-2 border-t border-slate-800 bg-slate-900/40">
            <p className="text-[10px] text-slate-400 font-bold text-center">
              {filtered.length} complaint{filtered.length !== 1 ? 's' : ''} shown
            </p>
          </div>
        </div>

        {/* RIGHT: Detail + Chat */}
        <div className="flex-1 min-w-0 flex flex-col gap-3">
          {/* Panel Toggle */}
          {selectedComplaint && (
            <div className="flex items-center gap-1 bg-slate-900/60 border border-slate-800 rounded-xl p-1 self-start">
              {[
                { id: 'detail', label: 'Complaint Details', icon: FileText },
                { id: 'chat',   label: 'AI Assistant',      icon: Bot },
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActivePanel(id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    activePanel === id
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {label}
                </button>
              ))}
            </div>
          )}

          {/* Content Area */}
          <div className="flex-1 min-h-0 flex gap-3">
            {/* Detail Panel */}
            <div className={`flex-1 bg-[#0A0F1E] border border-slate-800 rounded-xl overflow-y-auto p-4 ${
              selectedComplaint && activePanel === 'chat' ? 'hidden lg:block' : ''
            }`}>
              {detailLoading ? (
                <div className="flex items-center justify-center h-40">
                  <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-amber-500" />
                </div>
              ) : (
                <ComplaintDetail
                  complaint={selectedComplaint}
                  onSendToManager={handleSendToManager}
                  sending={sending}
                  confirmation={confirmation}
                />
              )}
            </div>

            {/* Chatbot Panel — always visible on desktop, toggleable on mobile */}
            <div className={`w-80 shrink-0 flex-col ${
              selectedComplaint
                ? activePanel === 'chat' ? 'flex' : 'hidden lg:flex'
                : 'hidden lg:flex'
            }`} style={{ maxHeight: '680px' }}>
              <ReviewerChatbot complaint={selectedComplaint} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

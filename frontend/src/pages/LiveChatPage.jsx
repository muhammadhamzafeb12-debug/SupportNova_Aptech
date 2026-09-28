import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  MessageSquare, Send, Sparkles, Bot, User, CheckCircle2,
  FileText, ShieldCheck, RefreshCw, AlertCircle, ArrowRight, CornerDownLeft
} from 'lucide-react';

export const LiveChatPage = ({ onComplaintSubmitted }) => {
  const { user, token } = useAuth();
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: `Hello ${user?.full_name || 'Customer'}! I am SupportNova's AI Assistant. How can I help you today? You can ask me policy questions, troubleshoot an issue, or let me log a formal complaint for you.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      sources: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showComplaintCard, setShowComplaintCard] = useState(null);
  const [complaintSubmitting, setComplaintSubmitting] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, showComplaintCard]);

  const quickPrompts = [
    "Received damaged or defective item",
    "Request billing refund or overcharge review",
    "Package delayed past estimated delivery date",
    "What is NovaCart warranty & return policy?"
  ];

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/rag/query', {
        method: 'POST',
        headers,
        body: JSON.stringify({ query, top_k: 3 })
      });

      let botAnswer = "";
      let sources = [];

      if (res.ok) {
        const data = await res.json();
        botAnswer = data.answer || "I have analyzed your request against our policy guidelines.";
        sources = data.sources || [];
      } else {
        botAnswer = "I've logged your request. Would you like me to register an official support ticket for our compliance team to investigate?";
      }

      // Check if user is reporting a complaint or problem
      const lowerQuery = query.toLowerCase();
      const isComplaintIntent = lowerQuery.includes("damage") || lowerQuery.includes("defect") ||
                                lowerQuery.includes("refund") || lowerQuery.includes("delay") ||
                                lowerQuery.includes("complaint") || lowerQuery.includes("issue") ||
                                lowerQuery.includes("wrong") || lowerQuery.includes("broken") ||
                                lowerQuery.includes("return");

      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: botAnswer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: sources,
        offerTicket: isComplaintIntent,
        ticketPromptText: query
      };

      setMessages(prev => [...prev, botMsg]);

      if (isComplaintIntent) {
        setShowComplaintCard({
          title: `Issue reported: ${query.slice(0, 50)}...`,
          description: query,
          customer_type: 'REGULAR',
          order_ref: 'ORD-' + Math.floor(10000 + Math.random() * 90000)
        });
      }

    } catch (err) {
      console.error("Live chat query error:", err);
      setMessages(prev => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: "I am having trouble connecting to the RAG Policy engine right now. However, you can register a complaint ticket below and our support team will inspect it.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          offerTicket: true,
          ticketPromptText: query
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterTicket = async (e) => {
    e.preventDefault();
    if (!showComplaintCard) return;
    setComplaintSubmitting(true);

    try {
      const payload = {
        title: showComplaintCard.title,
        description: showComplaintCard.description,
        customer_type: showComplaintCard.customer_type || 'REGULAR',
        product_service: 'NovaCart Product Line',
        order_ref: showComplaintCard.order_ref || '',
        channel: 'CHAT',
        preferred_contact: 'EMAIL'
      };

      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/complaints', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error("Ticket registration failed.");
      const created = await res.json();

      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          sender: 'bot',
          text: `🎉 Official Complaint Ticket **${created.complaint_code}** has been registered successfully! Our Dual-Pipeline AI engine is currently analyzing your complaint.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          createdId: created.id
        }
      ]);

      setShowComplaintCard(null);
      if (onComplaintSubmitted) {
        onComplaintSubmitted(created.id);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to submit ticket. Please try again.");
    } finally {
      setComplaintSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4 animate-fade-in flex flex-col h-[calc(100vh-7rem)]">
      {/* Top Header */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-xl shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shadow-md">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              SupportNova AI Live Assistant
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                Online (RAG Active)
              </span>
            </h1>
            <p className="text-xs text-slate-400">Real-time intelligent support chat & instant ticket registration desk</p>
          </div>
        </div>

        <button
          onClick={() => {
            setMessages([
              {
                id: 1,
                sender: 'bot',
                text: `Hello ${user?.full_name || 'Customer'}! I am SupportNova's AI Assistant. How can I help you today? You can ask me policy questions, troubleshoot an issue, or let me log a formal complaint for you.`,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                sources: []
              }
            ]);
            setShowComplaintCard(null);
          }}
          className="p-2 rounded-lg text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all text-xs font-semibold flex items-center gap-1.5"
          title="Restart Chat"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">New Chat</span>
        </button>
      </div>

      {/* Main Chat Stream */}
      <div className="flex-1 bg-[#0D1322]/90 border border-slate-800 rounded-xl p-4 overflow-y-auto space-y-4 backdrop-blur-md shadow-xl">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start gap-3 ${m.sender === 'user' ? 'flex-row-reverse' : ''}`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 border ${
                m.sender === 'user'
                  ? 'bg-blue-600 text-white border-blue-400/30'
                  : 'bg-slate-800 text-blue-400 border-slate-700'
              }`}
            >
              {m.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            {/* Message Bubble */}
            <div className={`max-w-2xl space-y-2 ${m.sender === 'user' ? 'items-end' : ''}`}>
              <div
                className={`p-3.5 rounded-2xl text-xs leading-relaxed shadow-md ${
                  m.sender === 'user'
                    ? 'bg-blue-600 text-white rounded-tr-none'
                    : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none'
                }`}
              >
                <div className="whitespace-pre-wrap">{m.text}</div>

                {/* Sources list if returned by RAG */}
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800/80 space-y-1.5">
                    <div className="text-[10px] font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-amber-400" /> Grounded Policy Citation:
                    </div>
                    {m.sources.map((s, idx) => (
                      <div key={idx} className="bg-slate-950/60 p-2 rounded-lg text-[11px] text-slate-300 border border-slate-800/80">
                        <span className="font-semibold text-white">{s.document_title}</span>
                        <span className="text-slate-400 font-mono text-[10px] ml-1.5">({s.doc_id})</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div
                className={`text-[10px] text-slate-500 font-mono ${
                  m.sender === 'user' ? 'text-right' : 'text-left'
                }`}
              >
                {m.timestamp}
              </div>
            </div>
          </div>
        ))}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-blue-400">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl px-4 py-2.5 text-xs text-slate-400 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce"></span>
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.4s]"></span>
              <span className="font-mono text-[11px] text-blue-400 ml-1">Analyzing policy rules & context...</span>
            </div>
          </div>
        )}

        {/* Inline Formal Complaint Registration Card */}
        {showComplaintCard && (
          <div className="bg-slate-900 border border-blue-500/40 rounded-2xl p-5 space-y-4 shadow-2xl animate-fade-in my-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                <h3 className="text-xs font-bold text-white">Register Official Support Complaint Ticket</h3>
              </div>
              <span className="text-[10px] font-mono font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                Live Chat Intake
              </span>
            </div>

            <form onSubmit={handleRegisterTicket} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-400">Complaint Title</label>
                <input
                  type="text"
                  required
                  value={showComplaintCard.title}
                  onChange={(e) => setShowComplaintCard(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400">Customer Tier</label>
                  <select
                    value={showComplaintCard.customer_type}
                    onChange={(e) => setShowComplaintCard(prev => ({ ...prev, customer_type: e.target.value }))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="REGULAR">Regular Customer</option>
                    <option value="PREMIUM">Premium Account</option>
                    <option value="VIP">VIP Client</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400">Order Reference</label>
                  <input
                    type="text"
                    value={showComplaintCard.order_ref}
                    onChange={(e) => setShowComplaintCard(prev => ({ ...prev, order_ref: e.target.value }))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-400">Detailed Complaint Description</label>
                <textarea
                  rows="3"
                  required
                  value={showComplaintCard.description}
                  onChange={(e) => setShowComplaintCard(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-blue-500"
                ></textarea>
              </div>

              <div className="flex gap-2 pt-1">
                <button
                  type="submit"
                  disabled={complaintSubmitting}
                  className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl transition-all shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{complaintSubmitting ? 'Registering Ticket...' : 'Confirm & Register Ticket'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setShowComplaintCard(null)}
                  className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs rounded-xl transition-all"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Suggestion Prompt Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 shrink-0 scrollbar-none">
        {quickPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            disabled={loading}
            className="px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-blue-500/40 hover:bg-slate-800 text-[11px] font-medium transition-all shrink-0 flex items-center gap-1.5"
          >
            <Sparkles className="w-3 h-3 text-blue-400" />
            <span>{prompt}</span>
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="relative shrink-0"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe your issue or ask a question..."
          className="w-full bg-[#0D1322] border border-slate-800 rounded-xl pl-4 pr-12 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 shadow-xl"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="absolute right-2 top-2 p-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white transition-all shadow-md shadow-blue-500/20"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};

export default LiveChatPage;

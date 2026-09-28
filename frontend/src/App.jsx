import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ComplaintsListPage } from './pages/ComplaintsListPage';
import { SubmitComplaintPage } from './pages/SubmitComplaintPage';
import { LiveChatPage } from './pages/LiveChatPage';
import { EmailIntakePage } from './pages/EmailIntakePage';
import { ComplaintDetailPage } from './pages/ComplaintDetailPage';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { RuleMatrixPage } from './pages/RuleMatrixPage';
import { ManualReviewPage } from './pages/ManualReviewPage';
import { SLAPage } from './pages/SLAPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ReportsPage } from './pages/ReportsPage';
import { PromptManagementPage } from './pages/PromptManagementPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { UserManagementPage } from './pages/UserManagementPage';
import { ReviewerDashboard } from './pages/ReviewerDashboard';
import { ShieldAlert, Menu, X, LayoutDashboard, FileText, PlusCircle, Shield, BookOpen, Grid, Clock, BarChart3, Download, Users, Terminal, History, CheckCircle2, ArrowRight, Sparkles, UserCheck, ShieldCheck } from 'lucide-react';

const ROLE_DETAILS = {
  AGENT: {
    title: "Support Agent Profile Active",
    subtitle: "Customer Service & Complaint Resolution Operational Desk",
    email: "agent@novacart.com",
    badge: "TIER-1 & TIER-2 AGENT",
    badgeColor: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    description: "As a Support Agent, you handle incoming customer tickets, analyze complaint descriptions, consult RAG policy guidelines, and resolve cases within SLA deadlines.",
    capabilities: [
      "View and triage customer complaint tickets",
      "Run GenAI Policy & Ground-Truth rule analysis",
      "Access RAG Knowledge Base and policy documents",
      "Track response and resolution SLA deadlines"
    ],
    recommendedTab: "dashboard",
    tabLabel: "Open Agent Dashboard"
  },
  REVIEWER: {
    title: "Manual Reviewer & Compliance Auditor Active",
    subtitle: "Ground-Truth Verification & Policy Oversight Desk",
    email: "reviewer@novacart.com",
    badge: "COMPLIANCE & AUDIT",
    badgeColor: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    description: "As a Manual Reviewer, your primary responsibility is auditing complaints where GenAI Pipeline 1 output differed from Python Ground-Truth Pipeline 2 verification.",
    capabilities: [
      "Access Manual Review Queue for flagged complaints",
      "Override or approve AI routing and priority decisions",
      "Audit policy citations against company rule matrix",
      "Resolve P0 Critical and P1 High escalated disputes"
    ],
    recommendedTab: "reviews",
    tabLabel: "Open Reviewer Dashboard"
  },
  MANAGER: {
    title: "Department Manager Profile Active",
    subtitle: "Operations Leadership & System Analytics Hub",
    email: "manager@novacart.com",
    badge: "OPERATIONS MANAGEMENT",
    badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    description: "As a Department Manager, you oversee resolution accuracy, team productivity, overall SLA compliance rates, and system verification scores.",
    capabilities: [
      "Monitor overall complaint volumes and agreement rates",
      "Analyze department SLA performance and bottleneck trends",
      "Generate and export PDF & CSV executive reports",
      "Review 100-case GenAI vs Python evaluation reports"
    ],
    recommendedTab: "analytics",
    tabLabel: "Open Manager Analytics"
  },
  ADMIN: {
    title: "System Administrator Profile Active",
    subtitle: "Enterprise Governance, User RBAC & Prompt Control",
    email: "admin@novacart.com",
    badge: "FULL SYSTEM ADMIN",
    badgeColor: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    description: "As a System Administrator, you have unrestricted access to manage platform users, configure LLM system prompts, and inspect security audit logs.",
    capabilities: [
      "Manage system users, roles, and account statuses",
      "Tune and update GenAI LLM prompt templates",
      "Inspect immutable security audit log history",
      "Full administrative access across all 12 platform modules"
    ],
    recommendedTab: "users",
    tabLabel: "Open Admin Control Center"
  }
};

const AppContent = () => {
  const { user, token, loading } = useAuth();

  // Derive default tab from role stored in localStorage so it's available on first render
  const getDefaultTab = () => {
    try {
      const saved = localStorage.getItem('supportnova_user');
      if (saved) {
        const u = JSON.parse(saved);
        if (u.role === 'REVIEWER') return 'reviews';
      }
    } catch { /* ignore */ }
    return 'dashboard';
  };

  const [activeTab, setActiveTab] = useState(getDefaultTab);
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [switchedRoleModal, setSwitchedRoleModal] = useState(null);

  // When user role changes (e.g. after role switch), reset to correct default tab
  useEffect(() => {
    if (user?.role === 'REVIEWER' && activeTab === 'dashboard') {
      setActiveTab('reviews');
    }
  }, [user?.role]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#060911] flex items-center justify-center text-slate-400">
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto"></div>
          <p className="text-xs font-mono text-blue-400 tracking-wider">Initializing SupportNova Security Context...</p>
        </div>
      </div>
    );
  }

  // Mandatory Login Enforcer
  if (!user || !token) {
    return <LoginPage />;
  }

  const handleSelectComplaint = (id) => {
    setSelectedComplaintId(id);
    setActiveTab('detail');
  };

  // RBAC Permission Checker for Navigation Guard
  const canAccessTab = (tabId) => {
    const role = user.role;
    if (role === 'ADMIN') return true;

    const permissions = {
      dashboard: ['CUSTOMER', 'AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'],
      complaints: ['AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'],
      submit: ['CUSTOMER', 'AGENT', 'MANAGER', 'ADMIN'],
      'submit-web': ['CUSTOMER', 'AGENT', 'MANAGER', 'ADMIN'],
      'submit-email': ['CUSTOMER', 'AGENT', 'MANAGER', 'ADMIN'],
      'submit-chat': ['CUSTOMER', 'AGENT', 'MANAGER', 'ADMIN'],
      'submit-upload': ['CUSTOMER', 'AGENT', 'MANAGER', 'ADMIN'],
      detail: ['CUSTOMER', 'AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'],
      knowledge: ['AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'],
      rules: ['AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'],
      reviews: ['REVIEWER', 'MANAGER', 'ADMIN'],
      sla: ['AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'],
      analytics: ['MANAGER', 'ADMIN'],
      reports: ['MANAGER', 'ADMIN'],
      prompts: ['ADMIN'],
      users: ['ADMIN'],
      audit: ['ADMIN']
    };

    return permissions[tabId] ? permissions[tabId].includes(role) : false;
  };

  const renderContent = () => {
    if (!canAccessTab(activeTab)) {
      return (
        <div className="p-8 rounded-2xl bg-[#0D1322] border border-rose-500/30 text-center space-y-4 max-w-xl mx-auto my-12 shadow-2xl">
          <ShieldAlert className="w-12 h-12 text-rose-400 mx-auto animate-bounce" />
          <h2 className="text-xl font-bold text-white">403 — Access Prohibited</h2>
          <p className="text-xs text-slate-300 leading-relaxed">
            Your current role profile (<strong className="text-blue-400">{user.role}</strong>) does not have authorization to access this module.
          </p>
          <button
            onClick={() => setActiveTab('dashboard')}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-all shadow-lg shadow-blue-500/20"
          >
            Return to {user.role} Dashboard
          </button>
        </div>
      );
    }

    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage onSelectComplaint={handleSelectComplaint} onNavigate={setActiveTab} />;
      case 'complaints':
        return <ComplaintsListPage onSelectComplaint={handleSelectComplaint} onNavigate={setActiveTab} />;
      case 'submit':
      case 'submit-web':
        return <SubmitComplaintPage initialChannel="WEB_FORM" onComplaintSubmitted={(id) => handleSelectComplaint(id)} />;
      case 'submit-email':
        return <EmailIntakePage onComplaintSubmitted={(id) => handleSelectComplaint(id)} />;
      case 'submit-chat':
        return <LiveChatPage onComplaintSubmitted={(id) => handleSelectComplaint(id)} />;
      case 'submit-upload':
        return <SubmitComplaintPage initialChannel="UPLOADED_COMPLAINT" onComplaintSubmitted={(id) => handleSelectComplaint(id)} />;
      case 'detail':
        return <ComplaintDetailPage complaintId={selectedComplaintId} onBack={() => setActiveTab('complaints')} onNavigate={setActiveTab} />;
      case 'knowledge':
        return <KnowledgeBasePage />;
      case 'rules':
        return <RuleMatrixPage />;
      case 'reviews':
        // Reviewers get the new full Reviewer Dashboard; Managers/Admins keep the Manual Review Queue
        if (user?.role === 'REVIEWER') {
          return <ReviewerDashboard />;
        }
        return <ManualReviewPage onSelectComplaint={handleSelectComplaint} />;
      case 'sla':
        return <SLAPage />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'reports':
        return <ReportsPage />;
      case 'prompts':
        return <PromptManagementPage />;
      case 'users':
        return <UserManagementPage />;
      case 'audit':
        return <AuditLogsPage />;
      default:
        return <DashboardPage onSelectComplaint={handleSelectComplaint} onNavigate={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#060911] text-slate-100 flex flex-col font-sans">
      <Header />
      
      {/* Mobile Navigation Header Bar */}
      <div className="md:hidden bg-[#0D1322] border-b border-slate-800 px-4 py-2.5 flex items-center justify-between z-30">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 rounded-lg text-slate-300 hover:text-white bg-slate-900 border border-slate-800 flex items-center gap-2 text-xs font-bold"
        >
          {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          <span>Menu</span>
        </button>
        <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">
          {activeTab}
        </span>
      </div>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#0D1322] border-b border-slate-800 p-4 space-y-2 z-30 animate-fade-in">
          <div className="grid grid-cols-2 gap-2">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
              { id: 'complaints', label: 'Complaints', icon: FileText },
              { id: 'submit-web', label: 'Submit Intake', icon: PlusCircle },
              { id: 'reviews', label: 'Manual Reviews', icon: Shield },
              { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen },
              { id: 'rules', label: 'Rule Matrix', icon: Grid },
              { id: 'sla', label: 'SLA Tracker', icon: Clock },
              { id: 'analytics', label: 'Analytics', icon: BarChart3 },
              { id: 'reports', label: 'Reports', icon: Download },
              { id: 'users', label: 'Users', icon: Users },
              { id: 'prompts', label: 'Prompts', icon: Terminal },
              { id: 'audit', label: 'Audit Logs', icon: History }
            ].filter((item) => canAccessTab(item.id)).map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`flex items-center gap-2 p-2 rounded-lg text-xs font-semibold ${
                    activeTab === item.id ? 'bg-blue-600 text-white' : 'bg-slate-900 text-slate-300'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="flex-1 flex">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onRoleSwitched={(roleKey) => setSwitchedRoleModal(roleKey)}
        />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          {renderContent()}
        </main>
      </div>

      {/* Role Profile Switched Modal */}
      {switchedRoleModal && ROLE_DETAILS[switchedRoleModal] && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-[#0D1322] border border-blue-500/30 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl relative">
            <button
              onClick={() => setSwitchedRoleModal(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <UserCheck className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-white">
                    {ROLE_DETAILS[switchedRoleModal].title}
                  </h3>
                </div>
                <p className="text-xs text-slate-400">
                  {ROLE_DETAILS[switchedRoleModal].subtitle}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
              <span className="text-slate-400 font-medium">Logged in User:</span>
              <span className="font-mono font-bold text-blue-400">{ROLE_DETAILS[switchedRoleModal].email}</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${ROLE_DETAILS[switchedRoleModal].badgeColor}`}>
                {ROLE_DETAILS[switchedRoleModal].badge}
              </span>
            </div>

            <div className="space-y-2">
              <p className="text-xs text-slate-300 leading-relaxed">
                {ROLE_DETAILS[switchedRoleModal].description}
              </p>
            </div>

            <div className="space-y-2 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                Unlocked Capabilities & Modules:
              </p>
              <div className="space-y-1.5">
                {ROLE_DETAILS[switchedRoleModal].capabilities.map((cap, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-200">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{cap}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => {
                  setActiveTab(ROLE_DETAILS[switchedRoleModal].recommendedTab);
                  setSwitchedRoleModal(null);
                }}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl transition-all shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2"
              >
                <span>{ROLE_DETAILS[switchedRoleModal].tabLabel}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const App = () => (
  <AuthProvider>
    <AppContent />
  </AuthProvider>
);

export default App;

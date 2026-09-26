import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ComplaintsListPage } from './pages/ComplaintsListPage';
import { SubmitComplaintPage } from './pages/SubmitComplaintPage';
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
import { ShieldAlert, Menu, X, LayoutDashboard, FileText, PlusCircle, Shield, BookOpen, Grid, Clock, BarChart3, Download, Users, Terminal, History } from 'lucide-react';

const AppContent = () => {
  const { user, token, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
      complaints: ['CUSTOMER', 'AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'],
      submit: ['CUSTOMER', 'AGENT', 'ADMIN'],
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
        return <SubmitComplaintPage onComplaintSubmitted={(id) => handleSelectComplaint(id)} />;
      case 'detail':
        return <ComplaintDetailPage complaintId={selectedComplaintId} onBack={() => setActiveTab('complaints')} onNavigate={setActiveTab} />;
      case 'knowledge':
        return <KnowledgeBasePage />;
      case 'rules':
        return <RuleMatrixPage />;
      case 'reviews':
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
              { id: 'submit', label: 'Submit', icon: PlusCircle },
              { id: 'reviews', label: 'Reviews', icon: Shield },
              { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen },
              { id: 'rules', label: 'Rule Matrix', icon: Grid },
              { id: 'sla', label: 'SLA Tracker', icon: Clock },
              { id: 'analytics', label: 'Analytics', icon: BarChart3 },
              { id: 'reports', label: 'Reports', icon: Download },
              { id: 'users', label: 'Users', icon: Users },
              { id: 'prompts', label: 'Prompts', icon: Terminal },
              { id: 'audit', label: 'Audit Logs', icon: History }
            ].map((item) => {
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
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export const App = () => (
  <AuthProvider>
    <AppContent />
  </AuthProvider>
);

export default App;

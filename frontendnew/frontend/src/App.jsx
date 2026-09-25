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
import { ShieldAlert } from 'lucide-react';

const AppContent = () => {
  const { user, token, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        <div className="text-center space-y-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto"></div>
          <p className="text-xs font-mono">Initializing SupportNova Security Context...</p>
        </div>
      </div>
    );
  }

  // Mandatory Login Enforcer: If not authenticated, render LoginPage
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
        <div className="p-8 rounded-2xl glass-panel border border-rose-500/30 text-center space-y-3 max-w-xl mx-auto my-12">
          <ShieldAlert className="w-10 h-10 text-rose-400 mx-auto" />
          <h2 className="text-lg font-bold text-white">403 - Access Prohibited</h2>
          <p className="text-xs text-slate-300">
            Your current role (<strong className="text-indigo-400">{user.role}</strong>) does not have authorization to view this module.
          </p>
          <button
            onClick={() => setActiveTab('dashboard')}
            className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold"
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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header />
      <div className="flex-1 flex">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full">
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

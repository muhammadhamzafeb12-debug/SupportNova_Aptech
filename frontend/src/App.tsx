import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './routes/ProtectedRoute';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';

import { Login } from './pages/Login';
import { CustomerDashboard } from './pages/CustomerDashboard';
import { AgentDashboard } from './pages/AgentDashboard';
import { ReviewerQueue } from './pages/ReviewerQueue';
import { ManagerDashboard } from './pages/ManagerDashboard';
import { AdminKnowledgeBase } from './pages/AdminKnowledgeBase';
import { AdminRuleMatrix } from './pages/AdminRuleMatrix';
import { AdminAnalytics } from './pages/AdminAnalytics';
import { ComplaintSubmission } from './pages/ComplaintSubmission';

const DashboardLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 md:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard/customer" element={<CustomerDashboard />} />
            
            <Route
              path="/dashboard/agent"
              element={
                <ProtectedRoute allowedRoles={['Agent', 'Reviewer', 'Manager', 'Admin', 'Administrator']}>
                  <AgentDashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/reviewer-queue"
              element={
                <ProtectedRoute allowedRoles={['Reviewer', 'Manager', 'Admin', 'Administrator']}>
                  <ReviewerQueue />
                </ProtectedRoute>
              }
            />

            <Route
              path="/dashboard/manager"
              element={
                <ProtectedRoute allowedRoles={['Manager', 'Admin', 'Administrator']}>
                  <ManagerDashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin/knowledge-base"
              element={
                <ProtectedRoute allowedRoles={['Admin', 'Administrator']}>
                  <AdminKnowledgeBase />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin/rule-matrix"
              element={
                <ProtectedRoute allowedRoles={['Admin', 'Administrator', 'Manager']}>
                  <AdminRuleMatrix />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin/analytics"
              element={
                <ProtectedRoute allowedRoles={['Admin', 'Administrator', 'Manager']}>
                  <AdminAnalytics />
                </ProtectedRoute>
              }
            />

            <Route path="/submit-complaint" element={<ComplaintSubmission />} />

            <Route path="/" element={<Navigate to="/login" replace />} />
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;

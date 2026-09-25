import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-300">
        <div className="flex items-center space-x-3">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
          <span>Authenticating SupportNova session...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    const userRoleNorm = user.role.toLowerCase().trim();
    const allowedNorm = allowedRoles.map(r => r.toLowerCase().trim());
    
    // Normalize admin / administrator
    if (allowedNorm.includes('admin') && !allowedNorm.includes('administrator')) allowedNorm.push('administrator');
    if (allowedNorm.includes('administrator') && !allowedNorm.includes('admin')) allowedNorm.push('admin');

    if (!allowedNorm.includes(userRoleNorm)) {
      if (userRoleNorm === 'customer') return <Navigate to="/dashboard/customer" replace />;
      if (userRoleNorm === 'agent') return <Navigate to="/dashboard/agent" replace />;
      if (userRoleNorm === 'reviewer') return <Navigate to="/reviewer-queue" replace />;
      if (userRoleNorm === 'manager') return <Navigate to="/dashboard/manager" replace />;
      if (userRoleNorm === 'admin' || userRoleNorm === 'administrator') return <Navigate to="/admin/knowledge-base" replace />;
      return <Navigate to="/login" replace />;
    }
  }

  return <>{children}</>;
};

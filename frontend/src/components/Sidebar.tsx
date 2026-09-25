import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  PlusCircle, 
  BookOpen, 
  Sliders, 
  BarChart3, 
  ShieldAlert,
  UserCheck
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role.toLowerCase() || 'customer';

  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition ${
      isActive
        ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30 shadow-glow-brand'
        : 'text-slate-400 hover:text-white hover:bg-dark-surfaceHover'
    }`;

  return (
    <aside className="w-64 border-r border-dark-border bg-dark-bg p-4 flex flex-col justify-between hidden md:flex min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div>
          <div className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Main Menu</div>
          <nav className="space-y-1">
            {(role === 'customer') && (
              <NavLink to="/dashboard/customer" className={navItemClass}>
                <LayoutDashboard className="w-4 h-4" />
                <span>My Dashboard</span>
              </NavLink>
            )}

            {(role === 'agent' || role === 'reviewer' || role === 'manager' || role === 'admin' || role === 'administrator') && (
              <NavLink to="/dashboard/agent" className={navItemClass}>
                <UserCheck className="w-4 h-4" />
                <span>Agent Workspace</span>
              </NavLink>
            )}

            {(role === 'reviewer' || role === 'manager' || role === 'admin' || role === 'administrator') && (
              <NavLink to="/reviewer-queue" className={navItemClass}>
                <ShieldAlert className="w-4 h-4" />
                <span>Reviewer Queue</span>
              </NavLink>
            )}

            {(role === 'manager' || role === 'admin' || role === 'administrator') && (
              <NavLink to="/dashboard/manager" className={navItemClass}>
                <LayoutDashboard className="w-4 h-4" />
                <span>Manager Dashboard</span>
              </NavLink>
            )}

            <NavLink to="/submit-complaint" className={navItemClass}>
              <PlusCircle className="w-4 h-4" />
              <span>Submit Complaint</span>
            </NavLink>
          </nav>
        </div>

        {(role === 'admin' || role === 'administrator' || role === 'manager') && (
          <div>
            <div className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Administration</div>
            <nav className="space-y-1">
              <NavLink to="/admin/knowledge-base" className={navItemClass}>
                <BookOpen className="w-4 h-4 text-brand-400" />
                <span>Knowledge Base</span>
              </NavLink>
              <NavLink to="/admin/rule-matrix" className={navItemClass}>
                <Sliders className="w-4 h-4" />
                <span>Rule Matrix</span>
              </NavLink>
              <NavLink to="/admin/analytics" className={navItemClass}>
                <BarChart3 className="w-4 h-4" />
                <span>Analytics & Reports</span>
              </NavLink>
            </nav>
          </div>
        )}
      </div>

      <div className="bg-dark-surface border border-dark-border rounded-xl p-3 text-center">
        <div className="text-[11px] font-bold text-white flex items-center justify-center space-x-1">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-glow-active" />
          <span>Dual-Pipeline Engine 2.0</span>
        </div>
        <div className="text-[10px] text-slate-400 mt-0.5">GenAI + Ground-Truth Rules</div>
      </div>
    </aside>
  );
};

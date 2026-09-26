import React from 'react';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, FileText, PlusCircle, BookOpen, Grid, ShieldAlert,
  Clock, BarChart3, Download, Terminal, History, Users, Sparkles, Sliders
} from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab }) => {
  const { user } = useAuth();
  const role = user?.role || 'CUSTOMER';

  const menuSections = [
    {
      title: 'WORKSPACE',
      items: [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['CUSTOMER', 'AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'] },
        { id: 'complaints', label: 'Complaints Queue', icon: FileText, roles: ['CUSTOMER', 'AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'] },
        { id: 'submit', label: 'Submit Complaint', icon: PlusCircle, roles: ['CUSTOMER', 'AGENT', 'ADMIN'] },
        { id: 'reviews', label: 'Manual Review Queue', icon: ShieldAlert, roles: ['REVIEWER', 'MANAGER', 'ADMIN'] },
      ]
    },
    {
      title: 'AI ENGINE & RULES',
      items: [
        { id: 'knowledge', label: 'AI Policy Base', icon: BookOpen, roles: ['AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'] },
        { id: 'rules', label: 'Verification Matrix', icon: Grid, roles: ['AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'] },
      ]
    },
    {
      title: 'ANALYTICS & METRICS',
      items: [
        { id: 'analytics', label: 'Analytics & Trends', icon: BarChart3, roles: ['MANAGER', 'ADMIN'] },
        { id: 'sla', label: 'SLA Performance', icon: Clock, roles: ['AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'] },
        { id: 'reports', label: 'Reports & CSV Exports', icon: Download, roles: ['MANAGER', 'ADMIN'] },
      ]
    },
    {
      title: 'ADMINISTRATION',
      items: [
        { id: 'users', label: 'User Management', icon: Users, roles: ['ADMIN'] },
        { id: 'prompts', label: 'Prompt Management', icon: Terminal, roles: ['ADMIN'] },
        { id: 'audit', label: 'Audit Log History', icon: History, roles: ['ADMIN'] },
      ]
    }
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-[#060911]/95 p-4 flex flex-col justify-between hidden md:flex shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        {menuSections.map((section, idx) => {
          const visibleItems = section.items.filter(item => item.roles.includes(role));
          if (visibleItems.length === 0) return null;

          return (
            <div key={idx} className="space-y-1.5">
              <h3 className="px-3 text-[10px] font-extrabold tracking-widest text-slate-400 uppercase mb-1.5 flex items-center justify-between">
                <span>{section.title}</span>
              </h3>
              <nav className="space-y-1">
                {visibleItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 text-left relative group ${
                        isActive
                          ? 'bg-blue-600/15 text-white border border-blue-500/30 shadow-md shadow-blue-500/10'
                          : 'text-slate-400 hover:text-white hover:bg-slate-900/80 hover:translate-x-1'
                      }`}
                    >
                      {isActive && (
                        <span className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full bg-blue-500 shadow-sm shadow-blue-500"></span>
                      )}
                      <Icon className={`w-4 h-4 transition-transform duration-200 group-hover:scale-110 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
          );
        })}
      </div>

      {/* Footer Badge */}
      <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between px-3 bg-slate-900/60 rounded-xl p-2.5 border border-slate-800">
        <span className="flex items-center gap-1.5 font-medium">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" /> Ground-Truth v1.0
        </span>
        <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          Active
        </span>
      </div>
    </aside>
  );
};

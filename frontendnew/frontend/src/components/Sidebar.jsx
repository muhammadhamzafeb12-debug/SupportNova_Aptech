import React from 'react';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, FileText, PlusCircle, BookOpen, Grid, ShieldAlert,
  Clock, BarChart3, Download, Terminal, History, Users
} from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab }) => {
  const { user } = useAuth();
  const role = user?.role || 'CUSTOMER';

  const menuSections = [
    {
      title: 'WORKSPACE',
      items: [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['CUSTOMER', 'AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'] },
        { id: 'complaints', label: 'Complaints', icon: FileText, roles: ['CUSTOMER', 'AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'] },
        { id: 'submit', label: 'Submit Complaint', icon: PlusCircle, roles: ['CUSTOMER', 'AGENT', 'ADMIN'] },
        { id: 'reviews', label: 'Manual Review', icon: ShieldAlert, roles: ['REVIEWER', 'MANAGER', 'ADMIN'] },
      ]
    },
    {
      title: 'KNOWLEDGE',
      items: [
        { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen, roles: ['AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'] },
        { id: 'rules', label: 'Rule Matrix', icon: Grid, roles: ['AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'] },
      ]
    },
    {
      title: 'INSIGHTS',
      items: [
        { id: 'analytics', label: 'Analytics & Trends', icon: BarChart3, roles: ['MANAGER', 'ADMIN'] },
        { id: 'sla', label: 'SLA Tracker', icon: Clock, roles: ['AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'] },
        { id: 'reports', label: 'Reports', icon: Download, roles: ['MANAGER', 'ADMIN'] },
      ]
    },
    {
      title: 'ADMINISTRATION',
      items: [
        { id: 'users', label: 'User Management', icon: Users, roles: ['ADMIN'] },
        { id: 'prompts', label: 'Prompt Management', icon: Terminal, roles: ['ADMIN'] },
        { id: 'audit', label: 'Audit Logs', icon: History, roles: ['ADMIN'] },
      ]
    }
  ];

  return (
    <aside className="w-64 border-r border-[#202838] bg-[#101521] p-4 flex flex-col justify-between hidden md:flex shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        {menuSections.map((section, idx) => {
          const visibleItems = section.items.filter(item => item.roles.includes(role));
          if (visibleItems.length === 0) return null;

          return (
            <div key={idx} className="space-y-1">
              <h3 className="px-3 text-[11px] font-semibold tracking-wider text-[#98A2B3] uppercase mb-2">
                {section.title}
              </h3>
              <nav className="space-y-0.5">
                {visibleItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-colors text-left ${
                        isActive
                          ? 'bg-[#151B28] text-[#F4F6FA] border-l-2 border-[#635BFF]'
                          : 'text-[#98A2B3] hover:text-[#F4F6FA] hover:bg-[#151B28]'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? 'text-[#635BFF]' : 'text-[#98A2B3]'}`} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
          );
        })}
      </div>

      {/* System Status Footer */}
      <div className="pt-4 border-t border-[#202838] text-[11px] text-[#98A2B3] flex items-center justify-between px-3">
        <span>System Status</span>
        <span className="flex items-center gap-1.5 text-[#22C55E] font-medium">
          <span className="w-2 h-2 rounded-full bg-[#22C55E]"></span>
          Operational
        </span>
      </div>
    </aside>
  );
};

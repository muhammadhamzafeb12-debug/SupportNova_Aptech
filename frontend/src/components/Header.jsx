import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck, Search, Bell, LogOut, ChevronDown, UserCheck, Sparkles, Activity, User, Check
} from 'lucide-react';

export const Header = () => {
  const { user, logout, switchRoleDemo } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const dropdownRef = useRef(null);
  const notifRef = useRef(null);

  const roles = [
    { id: 'CUSTOMER', label: 'Customer' },
    { id: 'AGENT', label: 'Agent' },
    { id: 'REVIEWER', label: 'Reviewer' },
    { id: 'MANAGER', label: 'Manager' },
    { id: 'ADMIN', label: 'Admin' },
  ];

  const notifications = [
    { id: 1, title: 'New Complaint Submitted', time: '5m ago', unread: true },
    { id: 2, title: 'Verification Score Mismatch Flagged', time: '18m ago', unread: true },
    { id: 3, title: 'SLA Target Warning (CMP-2026004)', time: '1h ago', unread: false }
  ];

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectRole = async (roleId) => {
    setDropdownOpen(false);
    if (switchRoleDemo) {
      await switchRoleDemo(roleId);
    }
  };

  const getRoleBadgeStyle = (role) => {
    switch (role) {
      case 'ADMIN': return 'bg-purple-500/15 text-purple-400 border-purple-500/30';
      case 'MANAGER': return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
      case 'REVIEWER': return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'AGENT': return 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30';
      case 'CUSTOMER': return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      default: return 'bg-slate-700/50 text-slate-300 border-slate-600';
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-[#060911]/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40 shadow-lg">
      {/* Left Branding & Quick Search */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-blue-500/25 border border-blue-400/30">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg text-white tracking-tight flex items-center gap-1.5">
              Support<span className="text-blue-500">Nova</span>
            </span>
          </div>
        </div>

        {/* Global Search Bar */}
        <div className="hidden md:flex items-center relative w-64 lg:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search complaints, rules, policies..."
            className="w-full bg-slate-900/90 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>
      </div>

      {/* Right Controls: Notifications, Role Selector, User Profile */}
      <div className="flex items-center gap-4">
        {/* Dual-Pipeline Engine Badge */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          <span>Engine Status: <strong className="text-emerald-400">ONLINE (Dual-Pipeline)</strong></span>
        </div>

        {/* Notifications Popover */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setNotifOpen(!notifOpen)}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-all relative"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-blue-500"></span>
          </button>

          {notifOpen && (
            <div className="absolute right-0 mt-2 w-80 rounded-xl bg-[#0D1322] border border-slate-800 shadow-2xl py-2 z-50 animate-fade-in backdrop-blur-xl">
              <div className="px-4 py-2 border-b border-slate-800 flex items-center justify-between">
                <span className="text-xs font-bold text-white">System Notifications</span>
                <span className="text-[10px] font-semibold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">3 New</span>
              </div>
              <div className="divide-y divide-slate-800/60 max-h-64 overflow-y-auto">
                {notifications.map((n) => (
                  <div key={n.id} className="p-3 hover:bg-slate-900/80 transition-colors cursor-pointer text-xs space-y-1">
                    <div className="flex items-center justify-between text-slate-200 font-semibold">
                      <span>{n.title}</span>
                      {n.unread && <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>}
                    </div>
                    <div className="text-[10px] text-slate-400">{n.time}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Role Profile Switcher Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${getRoleBadgeStyle(user?.role)}`}
          >
            <span className="text-slate-400 font-normal">Role:</span>
            <span className="font-extrabold tracking-wider">{user?.role || 'SELECT'}</span>
            <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-52 rounded-xl bg-[#0D1322] border border-slate-800 shadow-2xl py-1 z-50 animate-fade-in backdrop-blur-xl">
              <div className="px-3.5 py-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                Switch Role Profile
              </div>
              {roles.map((r) => (
                <button
                  key={r.id}
                  onClick={() => handleSelectRole(r.id)}
                  className={`w-full text-left px-3.5 py-2.5 text-xs flex items-center justify-between hover:bg-slate-900 transition-colors ${
                    user?.role === r.id ? 'text-blue-400 font-bold bg-blue-500/10' : 'text-slate-200'
                  }`}
                >
                  <span>{r.label}</span>
                  {user?.role === r.id && <UserCheck className="w-4 h-4 text-blue-400" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* User Profile Info & Logout */}
        {user ? (
          <div className="flex items-center gap-3 border-l border-slate-800 pl-4">
            <div className="w-8 h-8 rounded-lg bg-blue-600 border border-blue-400/40 flex items-center justify-center text-white text-xs font-bold shadow-sm">
              {user.username ? user.username.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-bold text-white">{user.full_name || user.username}</div>
              <div className="text-[10px] font-mono text-slate-400 uppercase">{user.role}</div>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-all"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
};

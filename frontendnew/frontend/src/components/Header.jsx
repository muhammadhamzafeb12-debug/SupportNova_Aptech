import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, User, LogOut, ChevronDown, UserCheck } from 'lucide-react';

export const Header = () => {
  const { user, logout, switchRoleDemo } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const roles = [
    { id: 'CUSTOMER', label: 'Customer' },
    { id: 'AGENT', label: 'Agent' },
    { id: 'REVIEWER', label: 'Reviewer' },
    { id: 'MANAGER', label: 'Manager' },
    { id: 'ADMIN', label: 'Admin' },
  ];

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
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

  return (
    <header className="h-16 border-b border-[#202838] bg-[#101521] px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Left Branding */}
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 rounded-lg bg-[#635BFF] flex items-center justify-center text-white font-bold text-sm shadow-sm">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="flex items-center gap-2.5">
          <span className="font-bold text-lg text-[#F4F6FA] tracking-tight">SupportNova</span>
          <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-[#151B28] text-[#98A2B3] border border-[#202838]">
            ResponseX AI
          </span>
        </div>
      </div>

      {/* Right User & Demo Mode Controls */}
      <div className="flex items-center gap-4">
        {/* Demo Mode Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium bg-[#151B28] text-[#98A2B3] border border-[#202838] hover:text-[#F4F6FA] hover:border-slate-700 transition-colors"
          >
            <span>Demo Mode:</span>
            <span className="text-[#635BFF] font-semibold">{user?.role || 'Select'}</span>
            <ChevronDown className={`w-3.5 h-3.5 text-[#98A2B3] transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-44 rounded-md bg-[#101521] border border-[#202838] shadow-xl py-1 z-50">
              <div className="px-3 py-1.5 text-[11px] font-semibold text-[#98A2B3] uppercase tracking-wider border-b border-[#202838]">
                Switch Demo Role
              </div>
              {roles.map((r) => (
                <button
                  key={r.id}
                  onClick={() => handleSelectRole(r.id)}
                  className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-[#151B28] transition-colors ${
                    user?.role === r.id ? 'text-[#635BFF] font-semibold' : 'text-[#F4F6FA]'
                  }`}
                >
                  <span>{r.label}</span>
                  {user?.role === r.id && <UserCheck className="w-3.5 h-3.5 text-[#635BFF]" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* User Info & Profile */}
        {user ? (
          <div className="flex items-center gap-3 border-l border-[#202838] pl-4">
            <div className="w-8 h-8 rounded-full bg-[#151B28] border border-[#202838] flex items-center justify-center text-[#F4F6FA] text-xs font-medium">
              {user.username ? user.username.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-medium text-[#F4F6FA]">{user.full_name || user.username}</div>
              <div className="text-[11px] text-[#98A2B3]">{user.role}</div>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 rounded-md text-[#98A2B3] hover:text-[#EF4444] hover:bg-[#151B28] transition-colors ml-1"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
};

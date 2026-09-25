import React, { useState, useEffect } from 'react';
import { UserPlus, Power } from 'lucide-react';

export const UserManagementPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Add User state
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('AGENT');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('supportnova_token');
      const res = await fetch('/api/users', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) setUsers(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, full_name: fullName, password, role })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'User creation failed');
      }
      setSuccessMsg(`User '${username}' created successfully!`);
      setShowAddModal(false);
      setUsername('');
      setEmail('');
      setFullName('');
      setPassword('');
      await fetchUsers();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const handleUpdateRole = async (userId, newRole) => {
    try {
      const token = localStorage.getItem('supportnova_token');
      const res = await fetch(`/api/users/${userId}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ role: newRole })
      });
      if (res.ok) {
        setSuccessMsg(`Role updated to ${newRole}`);
        await fetchUsers();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleStatus = async (userId, currentStatus) => {
    try {
      const token = localStorage.getItem('supportnova_token');
      const res = await fetch(`/api/users/${userId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_active: !currentStatus })
      });
      if (res.ok) {
        setSuccessMsg(`User status updated.`);
        await fetchUsers();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#202838]">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
            User & Access Management
          </h1>
          <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
            Admin management panel for user roles, access control, and account status
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-[#635BFF] hover:bg-[#5249E6] text-white text-xs font-semibold rounded-md transition-colors flex items-center gap-2 shrink-0 shadow-sm"
        >
          <UserPlus className="w-4 h-4" />
          <span>Add User Account</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-md text-xs text-emerald-400">
          {successMsg}
        </div>
      )}

      {/* Users Table */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#98A2B3]">Loading user accounts...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-[#F4F6FA]">
              <thead className="bg-[#151B28] text-[#98A2B3] text-[11px] uppercase font-semibold border-b border-[#202838]">
                <tr>
                  <th className="p-3">ID</th>
                  <th className="p-3">User</th>
                  <th className="p-3">Email</th>
                  <th className="p-3">Role</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Last Login</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202838]">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-[#151B28]/50 transition-colors">
                    <td className="p-3 font-mono text-[#98A2B3]">#{u.id}</td>
                    <td className="p-3 font-medium text-[#F4F6FA]">
                      <div>{u.full_name}</div>
                      <div className="text-[11px] text-[#98A2B3]">@{u.username}</div>
                    </td>
                    <td className="p-3 text-[#98A2B3]">{u.email}</td>
                    <td className="p-3">
                      <select
                        value={u.role}
                        onChange={(e) => handleUpdateRole(u.id, e.target.value)}
                        className="bg-[#151B28] border border-[#202838] text-xs font-semibold text-[#635BFF] rounded px-2.5 py-1 focus:outline-none focus:border-[#635BFF]"
                      >
                        <option value="CUSTOMER">CUSTOMER</option>
                        <option value="AGENT">AGENT</option>
                        <option value="REVIEWER">REVIEWER</option>
                        <option value="MANAGER">MANAGER</option>
                        <option value="ADMIN">ADMIN</option>
                      </select>
                    </td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          u.is_active
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-red-500/10 text-red-400 border-red-500/20'
                        }`}
                      >
                        {u.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td className="p-3 text-[#98A2B3]">
                      {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => handleToggleStatus(u.id, u.is_active)}
                        className="px-2.5 py-1 rounded text-xs font-medium text-[#98A2B3] hover:text-[#F4F6FA] bg-[#151B28] border border-[#202838] transition-colors"
                      >
                        {u.is_active ? 'Disable' : 'Enable'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* CREATE USER MODAL */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-[#080B12]/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#101521] border border-[#202838] rounded-lg max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-[#202838] pb-3">
              <h3 className="text-sm font-semibold text-[#F4F6FA]">Create User Account</h3>
              <button onClick={() => setShowAddModal(false)} className="text-xs text-[#98A2B3] hover:text-[#F4F6FA]">
                Cancel
              </button>
            </div>

            {errorMsg && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-400">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleCreateUser} className="space-y-3">
              <div>
                <label className="text-xs text-[#98A2B3] font-medium block mb-1">Username</label>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-[#151B28] border border-[#202838] rounded px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                />
              </div>
              <div>
                <label className="text-xs text-[#98A2B3] font-medium block mb-1">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-[#151B28] border border-[#202838] rounded px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                />
              </div>
              <div>
                <label className="text-xs text-[#98A2B3] font-medium block mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-[#151B28] border border-[#202838] rounded px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                />
              </div>
              <div>
                <label className="text-xs text-[#98A2B3] font-medium block mb-1">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#151B28] border border-[#202838] rounded px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                />
              </div>
              <div>
                <label className="text-xs text-[#98A2B3] font-medium block mb-1">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-[#151B28] border border-[#202838] rounded px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                >
                  <option value="CUSTOMER">CUSTOMER</option>
                  <option value="AGENT">AGENT</option>
                  <option value="REVIEWER">REVIEWER</option>
                  <option value="MANAGER">MANAGER</option>
                  <option value="ADMIN">ADMIN</option>
                </select>
              </div>

              <button
                type="submit"
                className="w-full py-2 bg-[#635BFF] hover:bg-[#5249E6] text-white font-medium text-xs rounded transition-colors mt-2"
              >
                Create Account
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

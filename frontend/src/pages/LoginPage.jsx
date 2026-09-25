import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck, Check, Lock, User, Key, AlertTriangle, CheckCircle2, ArrowRight
} from 'lucide-react';

export const LoginPage = () => {
  const { login, register, quickDemoLogin, forgotPassword, resetPassword } = useAuth();

  const [isRegistering, setIsRegistering] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Login Form State
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);

  // Registration Form State
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regFullName, setRegFullName] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regRole, setRegRole] = useState('CUSTOMER');

  // Forgot Password State
  const [resetInput, setResetInput] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [resetStep, setResetStep] = useState(1);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!usernameOrEmail.trim() || !password.trim()) {
      setError('Please enter both email/username and password');
      return;
    }

    try {
      setLoading(true);
      await login(usernameOrEmail, password, rememberMe);
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = async (roleName) => {
    setError('');
    setSuccessMsg('');
    try {
      setLoading(true);
      await quickDemoLogin(roleName);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!regUsername || !regEmail || !regFullName || !regPassword) {
      setError('All registration fields are required');
      return;
    }

    try {
      setLoading(true);
      await register(regUsername, regEmail, regFullName, regPassword, regRole);
      setSuccessMsg('Account registered successfully! You can now log in.');
      setIsRegistering(false);
      setUsernameOrEmail(regUsername);
      setPassword(regPassword);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPasswordRequest = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    try {
      setLoading(true);
      const data = await forgotPassword(resetInput);
      setResetCode(data.demo_reset_code || `RESET-${resetInput.toUpperCase()}-2026`);
      setSuccessMsg(data.message || 'Reset code generated.');
      setResetStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPasswordSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    try {
      setLoading(true);
      await resetPassword(resetInput, newPassword);
      setSuccessMsg('Password updated successfully! Please log in with your new password.');
      setShowForgotPassword(false);
      setResetStep(1);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080B12] text-[#F4F6FA] flex items-center justify-center p-4 lg:p-8 font-sans">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        {/* LEFT COLUMN: Enterprise Overview */}
        <div className="space-y-6 lg:pr-8">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-[#635BFF] flex items-center justify-center text-white font-bold text-base shadow-sm">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-[#F4F6FA]">SupportNova</span>
          </div>

          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] leading-tight">
              Enterprise Complaint Resolution & Verification Platform
            </h1>
            <p className="mt-3 text-sm text-[#98A2B3] leading-relaxed">
              Resolve customer complaints faster with AI-assisted analysis, independent rule validation, and complete decision verification.
            </p>
          </div>

          <div className="space-y-3 pt-2 border-t border-[#202838]">
            <div className="flex items-start gap-3">
              <div className="w-5 h-5 rounded bg-[#151B28] border border-[#202838] flex items-center justify-center shrink-0 mt-0.5">
                <Check className="w-3.5 h-3.5 text-[#635BFF]" />
              </div>
              <div>
                <span className="text-sm font-medium text-[#F4F6FA]">AI-assisted complaint analysis</span>
                <p className="text-xs text-[#98A2B3]">Structured categorisation, sentiment detection, and policy extraction.</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-5 h-5 rounded bg-[#151B28] border border-[#202838] flex items-center justify-center shrink-0 mt-0.5">
                <Check className="w-3.5 h-3.5 text-[#635BFF]" />
              </div>
              <div>
                <span className="text-sm font-medium text-[#F4F6FA]">Independent rule-based verification</span>
                <p className="text-xs text-[#98A2B3]">Deterministic Python Ground-Truth validation against 100+ business rules.</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-5 h-5 rounded bg-[#151B28] border border-[#202838] flex items-center justify-center shrink-0 mt-0.5">
                <Check className="w-3.5 h-3.5 text-[#635BFF]" />
              </div>
              <div>
                <span className="text-sm font-medium text-[#F4F6FA]">Complete audit trail</span>
                <p className="text-xs text-[#98A2B3]">Full decision compliance score, manual review override, and immutable log history.</p>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Authentication Panel */}
        <div className="bg-[#101521] border border-[#202838] rounded-xl p-6 lg:p-8 space-y-6 shadow-xl">
          {/* Top Quick Demo Buttons */}
          <div className="bg-[#151B28] border border-[#202838] rounded-lg p-3 space-y-2">
            <div className="text-[11px] font-semibold text-[#98A2B3] uppercase tracking-wider">
              Quick Demo Access (RBAC Roles)
            </div>
            <div className="grid grid-cols-5 gap-1.5">
              {['CUSTOMER', 'AGENT', 'REVIEWER', 'MANAGER', 'ADMIN'].map((r) => (
                <button
                  key={r}
                  onClick={() => handleQuickDemo(r)}
                  disabled={loading}
                  className="py-1 px-1 bg-[#101521] hover:bg-[#635BFF] text-[#98A2B3] hover:text-white rounded border border-[#202838] text-[10px] font-semibold transition-colors truncate"
                  title={`Log in as ${r}`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Form Header */}
          <div className="flex items-center justify-between border-b border-[#202838] pb-3">
            <h2 className="text-base font-semibold text-[#F4F6FA]">
              {showForgotPassword
                ? 'Reset Password'
                : isRegistering
                ? 'Create Account'
                : 'Sign In'}
            </h2>
            {!showForgotPassword && (
              <button
                onClick={() => {
                  setIsRegistering(!isRegistering);
                  setError('');
                  setSuccessMsg('');
                }}
                className="text-xs text-[#635BFF] hover:underline font-medium"
              >
                {isRegistering ? 'Existing user? Sign In' : 'New user? Register'}
              </button>
            )}
          </div>

          {/* Alerts */}
          {error && (
            <div className="p-3 rounded-md bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* LOGIN FORM */}
          {!isRegistering && !showForgotPassword && (
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-[#98A2B3]">Username or Email</label>
                <div className="relative">
                  <User className="w-4 h-4 text-[#98A2B3] absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={usernameOrEmail}
                    onChange={(e) => setUsernameOrEmail(e.target.value)}
                    placeholder="admin"
                    className="w-full bg-[#151B28] border border-[#202838] rounded-md pl-9 pr-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-[#98A2B3]">Password</label>
                  <button
                    type="button"
                    onClick={() => setShowForgotPassword(true)}
                    className="text-xs text-[#635BFF] hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 text-[#98A2B3] absolute left-3 top-2.5" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-[#151B28] border border-[#202838] rounded-md pl-9 pr-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <label className="flex items-center gap-2 text-xs text-[#98A2B3] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded bg-[#151B28] border-[#202838] text-[#635BFF] focus:ring-0"
                  />
                  <span>Remember me</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 bg-[#635BFF] hover:bg-[#5249E6] text-white font-medium text-xs rounded-md transition-colors shadow-sm disabled:opacity-50"
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>
          )}

          {/* REGISTER FORM */}
          {isRegistering && !showForgotPassword && (
            <form onSubmit={handleRegister} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-[#98A2B3]">Username</label>
                  <input
                    type="text"
                    value={regUsername}
                    onChange={(e) => setRegUsername(e.target.value)}
                    placeholder="johndoe"
                    className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-[#98A2B3]">Role</label>
                  <select
                    value={regRole}
                    onChange={(e) => setRegRole(e.target.value)}
                    className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                  >
                    <option value="CUSTOMER">Customer</option>
                    <option value="AGENT">Agent</option>
                    <option value="REVIEWER">Reviewer</option>
                    <option value="MANAGER">Manager</option>
                    <option value="ADMIN">Admin</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-[#98A2B3]">Full Name</label>
                <input
                  type="text"
                  value={regFullName}
                  onChange={(e) => setRegFullName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-[#98A2B3]">Email Address</label>
                <input
                  type="email"
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  placeholder="john@novacart.com"
                  className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-[#98A2B3]">Password</label>
                <input
                  type="password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-1.5 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 bg-[#635BFF] hover:bg-[#5249E6] text-white font-medium text-xs rounded-md transition-colors mt-2"
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </button>
            </form>
          )}

          {/* FORGOT PASSWORD FORM */}
          {showForgotPassword && (
            <div className="space-y-4">
              {resetStep === 1 ? (
                <form onSubmit={handleForgotPasswordRequest} className="space-y-3">
                  <p className="text-xs text-[#98A2B3]">
                    Enter your registered email or username to generate a password reset code.
                  </p>
                  <input
                    type="text"
                    value={resetInput}
                    onChange={(e) => setResetInput(e.target.value)}
                    placeholder="Enter email or username"
                    className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                  />
                  <div className="flex gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowForgotPassword(false)}
                      className="w-1/2 py-2 px-3 bg-[#151B28] text-[#98A2B3] text-xs font-medium rounded-md hover:text-[#F4F6FA]"
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="w-1/2 py-2 px-3 bg-[#635BFF] text-white text-xs font-medium rounded-md hover:bg-[#5249E6]"
                    >
                      Get Code
                    </button>
                  </div>
                </form>
              ) : (
                <form onSubmit={handleResetPasswordSubmit} className="space-y-3">
                  <div className="p-2.5 rounded-md bg-[#151B28] border border-[#202838] text-xs space-y-1">
                    <div className="text-[10px] text-[#98A2B3]">Generated Reset Code:</div>
                    <div className="font-mono text-[#635BFF] font-bold select-all">{resetCode}</div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-[#98A2B3]">New Password</label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="New password (min 6 chars)"
                      className="w-full bg-[#151B28] border border-[#202838] rounded-md px-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 px-4 bg-[#635BFF] text-white font-medium text-xs rounded-md hover:bg-[#5249E6]"
                  >
                    Reset Password
                  </button>
                </form>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { useAuth, DEMO_CREDENTIALS } from '../context/AuthContext';
import {
  ShieldCheck, Check, Lock, User, AlertTriangle, CheckCircle2,
  Eye, EyeOff, HelpCircle, Sparkles, Shield, Cpu, Scale, History,
  Users, Server, Building2, LockKeyhole, ArrowRight, X
} from 'lucide-react';

export const LoginPage = () => {
  const { login, register, quickDemoLogin, forgotPassword, resetPassword } = useAuth();

  const [activeRoleTab, setActiveRoleTab] = useState('ADMIN');
  const [isRegistering, setIsRegistering] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [activeNavTab, setActiveNavTab] = useState('Home');
  const [showNavModal, setShowNavModal] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Form State
  const [usernameOrEmail, setUsernameOrEmail] = useState('admin');
  const [password, setPassword] = useState('admin123');
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

  // Handle Role Selector Switch
  const handleSelectRole = (roleKey) => {
    setActiveRoleTab(roleKey);
    setError('');
    setSuccessMsg('');
    const creds = DEMO_CREDENTIALS[roleKey];
    if (creds) {
      setUsernameOrEmail(creds.username);
      setPassword(creds.password);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!usernameOrEmail.trim() || !password.trim()) {
      setError('Please enter both username/email and password.');
      return;
    }

    try {
      setLoading(true);
      await login(usernameOrEmail, password, rememberMe);
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSSOLogin = async (provider) => {
    setError('');
    setSuccessMsg('');
    try {
      setLoading(true);
      setSuccessMsg(`Initiating secure ${provider} SSO handshake...`);
      setTimeout(async () => {
        try {
          await quickDemoLogin(activeRoleTab);
        } catch (err) {
          setError(err.message);
          setLoading(false);
        }
      }, 700);
    } catch (err) {
      setError(`${provider} authentication failed.`);
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!regUsername.trim() || !regEmail.trim() || !regFullName.trim() || !regPassword.trim()) {
      setError('All registration fields are required.');
      return;
    }

    try {
      setLoading(true);
      await register(regUsername, regEmail, regFullName, regPassword, regRole);
      setSuccessMsg('Account registered successfully! You may now sign in.');
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
      setSuccessMsg(data.message || 'Password reset token dispatched.');
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
      setSuccessMsg('Password updated successfully! Please log in with your new credentials.');
      setShowForgotPassword(false);
      setResetStep(1);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const rolesList = [
    { id: 'CUSTOMER', label: 'Customer' },
    { id: 'AGENT', label: 'Agent' },
    { id: 'REVIEWER', label: 'Reviewer' },
    { id: 'MANAGER', label: 'Manager' },
    { id: 'ADMIN', label: 'Admin' }
  ];

  return (
    <div className="min-h-screen bg-[#060911] text-[#F8FAFC] flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* ----------------- FIXED ENTERPRISE HEADER ----------------- */}
      <header className="sticky top-0 z-50 bg-[#060911]/85 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-8 py-3.5 flex items-center justify-between shadow-lg">
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/25 border border-blue-400/30">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-tight text-white">
              Support<span className="text-blue-500">Nova</span>
            </span>
            <span className="hidden sm:inline-block text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              v1.0 Enterprise
            </span>
          </div>
        </div>

        {/* Center Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-slate-300">
          {['Home', 'Features', 'About', 'Contact'].map((navItem) => (
            <button
              key={navItem}
              onClick={() => {
                setActiveNavTab(navItem);
                if (navItem !== 'Home') setShowNavModal(navItem);
              }}
              className={`transition-colors py-1 relative ${
                activeNavTab === navItem ? 'text-blue-400 font-bold' : 'hover:text-white'
              }`}
            >
              {navItem}
              {activeNavTab === navItem && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-full"></span>
              )}
            </button>
          ))}
        </nav>

        {/* Right CTA / Support Buttons */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowSupportModal(true)}
            className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <HelpCircle className="w-4 h-4 text-slate-400" />
            <span>Need Help?</span>
          </button>
          <button
            onClick={() => setShowSupportModal(true)}
            className="px-4 py-2 rounded-lg text-xs font-bold bg-slate-800/80 hover:bg-slate-700 text-white border border-slate-700/80 transition-all shadow-sm"
          >
            Get Support
          </button>
        </div>
      </header>

      {/* ----------------- SPLIT-SCREEN LANDING & AUTH ----------------- */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-10 flex items-center justify-center">
        <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
          
          {/* LEFT HERO SECTION (7 Columns) */}
          <div className="lg:col-span-7 space-y-8">
            {/* Tagline Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span>AI-Assisted Ground-Truth Complaint Resolution</span>
            </div>

            {/* Main Headline */}
            <div className="space-y-4">
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight leading-[1.15]">
                Enterprise Complaint Resolution & Verification Platform
              </h1>
              <p className="text-sm sm:text-base text-slate-300 leading-relaxed font-normal max-w-2xl">
                SupportNova empowers organizations to handle customer complaints with AI-assisted analysis, independent rule validation, and complete decision verification — faster, fairer, and more transparent.
              </p>
            </div>

            {/* 4 Feature Blocks */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              {/* Feature 1 */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2 hover:border-blue-500/30 transition-all">
                <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <Cpu className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-white">AI-Powered Analysis</h3>
                <p className="text-xs text-slate-400 leading-normal">
                  Detects patterns, flags risks, and suggests solutions automatically.
                </p>
              </div>

              {/* Feature 2 */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2 hover:border-blue-500/30 transition-all">
                <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                  <Scale className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-white">Independent Verification</h3>
                <p className="text-xs text-slate-400 leading-normal">
                  Ensures fair and rule-based decisions with Ground-Truth Python logic.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2 hover:border-blue-500/30 transition-all">
                <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <History className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-white">Complete Audit Trail</h3>
                <p className="text-xs text-slate-400 leading-normal">
                  Full transparency with detailed immutable decision logs.
                </p>
              </div>

              {/* Feature 4 */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2 hover:border-blue-500/30 transition-all">
                <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <Users className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-white">Multi-Role Access</h3>
                <p className="text-xs text-slate-400 leading-normal">
                  Tailored RBAC workflows for Customer, Agent, Reviewer, Manager & Admin.
                </p>
              </div>
            </div>

            {/* Compact Statistics / Trust Bar */}
            <div className="pt-4 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center sm:text-left">
              <div>
                <div className="text-lg font-extrabold text-blue-400">99%</div>
                <div className="text-[11px] text-slate-400 font-medium">Faster Resolution</div>
              </div>
              <div>
                <div className="text-lg font-extrabold text-cyan-400">100%</div>
                <div className="text-[11px] text-slate-400 font-medium">Data Security</div>
              </div>
              <div>
                <div className="text-lg font-extrabold text-emerald-400">24/7</div>
                <div className="text-[11px] text-slate-400 font-medium">Platform Uptime</div>
              </div>
              <div>
                <div className="text-lg font-extrabold text-white">500+</div>
                <div className="text-[11px] text-slate-400 font-medium">Trusted Enterprises</div>
              </div>
            </div>
          </div>

          {/* RIGHT LOGIN CARD (5 Columns) */}
          <div className="lg:col-span-5 w-full">
            <div className="bg-[#0D1322]/90 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl backdrop-blur-xl">
              
              {/* Card Header */}
              <div className="text-center space-y-2">
                <div className="w-12 h-12 rounded-xl bg-blue-600/15 border border-blue-500/30 mx-auto flex items-center justify-center text-blue-400">
                  <ShieldCheck className="w-7 h-7" />
                </div>
                <h2 className="text-xl font-bold text-white">Welcome Back</h2>
                <p className="text-xs text-slate-400">Sign in to your account to continue</p>
              </div>

              {/* Role Selector Pills */}
              <div className="space-y-1.5">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Select Role Profile</span>
                  <span className="text-[10px] text-blue-400 font-mono">Demo Mode</span>
                </div>
                <div className="grid grid-cols-5 gap-1.5 p-1 bg-slate-900/90 rounded-xl border border-slate-800">
                  {rolesList.map((r) => {
                    const isActive = activeRoleTab === r.id;
                    return (
                      <button
                        key={r.id}
                        type="button"
                        onClick={() => handleSelectRole(r.id)}
                        className={`py-1.5 text-[11px] font-bold rounded-lg transition-all truncate ${
                          isActive
                            ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30 border border-blue-400/40'
                            : 'text-slate-400 hover:text-white hover:bg-slate-800/80'
                        }`}
                      >
                        {r.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Error & Success Alert Banners */}
              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5 animate-fade-in">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <span className="leading-tight">{error}</span>
                </div>
              )}

              {successMsg && (
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-start gap-2.5 animate-fade-in">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="leading-tight">{successMsg}</span>
                </div>
              )}

              {/* SIGN IN FORM */}
              {!isRegistering && !showForgotPassword && (
                <form onSubmit={handleLogin} className="space-y-4">
                  {/* Username / Email */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Email or Username</label>
                    <div className="relative">
                      <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                      <input
                        type="text"
                        value={usernameOrEmail}
                        onChange={(e) => setUsernameOrEmail(e.target.value)}
                        placeholder="Enter your username or email"
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-lg pl-10 pr-3 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                      />
                    </div>
                  </div>

                  {/* Password */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-slate-300">Password</label>
                      <button
                        type="button"
                        onClick={() => {
                          setShowForgotPassword(true);
                          setError('');
                          setSuccessMsg('');
                        }}
                        className="text-xs text-blue-400 hover:text-blue-300 hover:underline font-medium"
                      >
                        Forgot password?
                      </button>
                    </div>
                    <div className="relative">
                      <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-lg pl-10 pr-10 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-200"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Remember Me */}
                  <div className="flex items-center justify-between pt-1">
                    <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        className="rounded bg-slate-900 border-slate-800 text-blue-600 focus:ring-0 w-3.5 h-3.5 cursor-pointer"
                      />
                      <span>Remember me</span>
                    </label>
                  </div>

                  {/* Sign In Button */}
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg transition-all shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {loading ? (
                      <span className="flex items-center gap-2">
                        <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                        Authenticating...
                      </span>
                    ) : (
                      <>
                        <span>Sign In</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>

                  {/* Divider */}
                  <div className="relative py-2">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-slate-800"></div>
                    </div>
                    <div className="relative flex justify-center text-[10px] uppercase">
                      <span className="bg-[#0D1322] px-2 text-slate-500 font-semibold">Or continue with</span>
                    </div>
                  </div>

                  {/* SSO Buttons */}
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => handleSSOLogin('Google')}
                      className="py-2 px-3 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
                    >
                      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                      </svg>
                      <span>Google</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleSSOLogin('Microsoft')}
                      className="py-2 px-3 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
                    >
                      <svg className="w-3.5 h-3.5" viewBox="0 0 23 23">
                        <path fill="#f35325" d="M1 1h10v10H1z"/>
                        <path fill="#81bc06" d="M12 1h10v10H12z"/>
                        <path fill="#05a6f0" d="M1 12h10v10H1z"/>
                        <path fill="#ffba08" d="M12 12h10v10H12z"/>
                      </svg>
                      <span>Microsoft</span>
                    </button>
                  </div>

                  {/* Toggle to Register */}
                  <div className="text-center pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setIsRegistering(true);
                        setError('');
                        setSuccessMsg('');
                      }}
                      className="text-xs text-slate-400 hover:text-white font-medium"
                    >
                      Don't have an account? <span className="text-blue-400 hover:underline">Register here</span>
                    </button>
                  </div>
                </form>
              )}

              {/* REGISTER FORM */}
              {isRegistering && !showForgotPassword && (
                <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-300">Username</label>
                      <input
                        type="text"
                        value={regUsername}
                        onChange={(e) => setRegUsername(e.target.value)}
                        placeholder="johndoe"
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-300">Role Profile</label>
                      <select
                        value={regRole}
                        onChange={(e) => setRegRole(e.target.value)}
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
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
                    <label className="text-xs font-semibold text-slate-300">Full Name</label>
                    <input
                      type="text"
                      value={regFullName}
                      onChange={(e) => setRegFullName(e.target.value)}
                      placeholder="John Doe"
                      className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-300">Email Address</label>
                    <input
                      type="email"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      placeholder="john@enterprise.com"
                      className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-300">Password</label>
                    <input
                      type="password"
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg transition-all mt-2"
                  >
                    {loading ? 'Creating Account...' : 'Create Account'}
                  </button>

                  <div className="text-center pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setIsRegistering(false);
                        setError('');
                        setSuccessMsg('');
                      }}
                      className="text-xs text-slate-400 hover:text-white"
                    >
                      Already registered? <span className="text-blue-400 hover:underline">Sign In</span>
                    </button>
                  </div>
                </form>
              )}

              {/* FORGOT PASSWORD FORM */}
              {showForgotPassword && (
                <div className="space-y-4">
                  {resetStep === 1 ? (
                    <form onSubmit={handleForgotPasswordRequest} className="space-y-3">
                      <p className="text-xs text-slate-300">
                        Enter your username or registered email to generate a password reset authorization token.
                      </p>
                      <input
                        type="text"
                        value={resetInput}
                        onChange={(e) => setResetInput(e.target.value)}
                        placeholder="Enter email or username"
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                      />
                      <div className="flex gap-2 pt-2">
                        <button
                          type="button"
                          onClick={() => {
                            setShowForgotPassword(false);
                            setError('');
                            setSuccessMsg('');
                          }}
                          className="w-1/2 py-2 px-3 bg-slate-800 text-slate-300 text-xs font-medium rounded-lg hover:text-white"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={loading}
                          className="w-1/2 py-2 px-3 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-500"
                        >
                          Generate Token
                        </button>
                      </div>
                    </form>
                  ) : (
                    <form onSubmit={handleResetPasswordSubmit} className="space-y-3">
                      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
                        <div className="text-[10px] text-slate-400">Generated Token:</div>
                        <div className="font-mono text-blue-400 font-bold select-all">{resetCode}</div>
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs font-semibold text-slate-300">New Password</label>
                        <input
                          type="password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          placeholder="New password (min 6 chars)"
                          className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-2.5 px-4 bg-blue-600 text-white font-bold text-xs rounded-lg hover:bg-blue-500"
                      >
                        Reset Password
                      </button>
                    </form>
                  )}
                </div>
              )}

              {/* Encrypted Login Indicator Badge */}
              <div className="pt-4 border-t border-slate-800/80 flex items-center justify-center gap-2 text-[11px] text-slate-400 font-medium">
                <LockKeyhole className="w-3.5 h-3.5 text-blue-400" />
                <span>256-Bit SSL Encrypted Enterprise Auth</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* ----------------- SUPPORT / HELP MODAL ----------------- */}
      {showSupportModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-[#0D1322] border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl relative">
            <button
              onClick={() => setShowSupportModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center">
                <HelpCircle className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white">SupportNova Assistance</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Need assistance accessing your SupportNova workspace? Contact our 24/7 Enterprise Support desk or try the built-in Quick Demo role buttons.
            </p>
            <div className="space-y-2 bg-slate-900 p-3 rounded-lg border border-slate-800 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Support Email:</span>
                <strong className="text-white">support@novacart.com</strong>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Enterprise Hotline:</span>
                <strong className="text-white">+1 (800) 555-NOVA</strong>
              </div>
            </div>
            <button
              onClick={() => setShowSupportModal(false)}
              className="w-full py-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-500"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* ----------------- NAVIGATION INFO MODAL ----------------- */}
      {showNavModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-[#0D1322] border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl relative">
            <button
              onClick={() => setShowNavModal(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-400" />
              <span>{showNavModal} — SupportNova Platform</span>
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              {showNavModal === 'Features' && 'SupportNova provides Dual-Pipeline AI complaint analysis, 100+ business rule Python Ground-Truth verification, automated SLA enforcement, and immutable audit logs.'}
              {showNavModal === 'About' && 'Developed for NovaCart Technologies, SupportNova ensures 100% compliant, fair, and unbiased complaint handling across multi-department enterprise teams.'}
              {showNavModal === 'Contact' && 'For enterprise licensing, integration inquiries, or custom rule engine deployment, contact enterprise@novacart.com.'}
            </p>
            <button
              onClick={() => setShowNavModal(null)}
              className="w-full py-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-500"
            >
              Got it
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 px-6 py-4 text-center text-xs text-slate-400">
        <p>© 2026 SupportNova Platform — NovaCart Technologies Inc. All Rights Reserved.</p>
      </footer>
    </div>
  );
};

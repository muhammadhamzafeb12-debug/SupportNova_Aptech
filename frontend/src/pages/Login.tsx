import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { GlowButton } from '../components/GlowButton';
import { ShieldCheck, Lock, Mail, ArrowRight, AlertCircle } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('customer@nexalink.com');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const user = await login(email, password);
      const role = user.role.toLowerCase();
      if (role === 'customer') navigate('/dashboard/customer');
      else if (role === 'agent') navigate('/dashboard/agent');
      else if (role === 'reviewer') navigate('/reviewer-queue');
      else if (role === 'manager') navigate('/dashboard/manager');
      else navigate('/admin/knowledge-base');
    } catch (err: any) {
      setError(err.message || 'Invalid credentials');
    } finally {
      setSubmitting(false);
    }
  };

  const quickRoles = [
    { label: 'Customer', email: 'customer@nexalink.com' },
    { label: 'Agent', email: 'agent@nexalink.com' },
    { label: 'Reviewer', email: 'reviewer@nexalink.com' },
    { label: 'Manager', email: 'manager@nexalink.com' },
    { label: 'Admin', email: 'admin@nexalink.com' },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg p-4 relative overflow-hidden font-sans">
      {/* Background Glow Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-violet/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md glass-card rounded-2xl p-8 border border-dark-border shadow-2xl relative z-10 animate-fade-slide-up">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-brand-gradient flex items-center justify-center mx-auto shadow-glow-brand mb-4">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">SupportNova AI</h2>
          <p className="text-xs text-slate-400 mt-1">Enterprise Customer Intelligence & Compliance Platform</p>
        </div>

        {error && (
          <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2.5 shadow-glow-expired">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-dark-bg border border-dark-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand-500"
                placeholder="user@nexalink.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-dark-bg border border-dark-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand-500"
                placeholder="••••••••"
              />
            </div>
          </div>

          <div className="pt-2">
            <GlowButton
              type="submit"
              loading={submitting}
              icon={<ArrowRight className="w-4 h-4" />}
              className="w-full py-3"
            >
              {submitting ? 'Signing in...' : 'Sign In to Portal'}
            </GlowButton>
          </div>
        </form>

        <div className="mt-8 pt-6 border-t border-dark-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 text-center mb-3">Quick Demo Role Shortcuts</div>
          <div className="flex flex-wrap gap-1.5 justify-center">
            {quickRoles.map((r) => (
              <button
                key={r.label}
                onClick={() => {
                  setEmail(r.email);
                  setPassword('password123');
                }}
                className="px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-dark-surface hover:bg-dark-surfaceHover text-slate-300 border border-dark-border hover:border-slate-600 transition"
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

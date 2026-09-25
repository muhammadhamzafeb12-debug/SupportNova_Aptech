import React from 'react';
import { Loader2 } from 'lucide-react';

interface GlowButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  loading?: boolean;
  icon?: React.ReactNode;
}

export const GlowButton: React.FC<GlowButtonProps> = ({
  children,
  variant = 'primary',
  loading = false,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  let baseStyle = "btn-brand-glow text-white font-semibold rounded-xl text-xs py-2 px-4 flex items-center justify-center space-x-2 transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg";

  if (variant === 'secondary') {
    baseStyle = "bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-xl text-xs py-2 px-4 flex items-center justify-center space-x-2 transition hover:border-slate-600 disabled:opacity-50";
  } else if (variant === 'danger') {
    baseStyle = "bg-rose-600 hover:bg-rose-500 text-white font-semibold rounded-xl text-xs py-2 px-4 flex items-center justify-center space-x-2 transition shadow-lg shadow-rose-500/20 disabled:opacity-50";
  } else if (variant === 'success') {
    baseStyle = "bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl text-xs py-2 px-4 flex items-center justify-center space-x-2 transition shadow-lg shadow-emerald-500/20 disabled:opacity-50";
  }

  return (
    <button
      disabled={disabled || loading}
      className={`${baseStyle} ${className}`}
      {...props}
    >
      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : icon}
      <span>{children}</span>
    </button>
  );
};

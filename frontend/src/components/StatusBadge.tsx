import React from 'react';
import { CheckCircle2, Clock, FileCheck, AlertOctagon, AlertTriangle } from 'lucide-react';

interface StatusBadgeProps {
  status: string;
  type?: 'status' | 'priority' | 'role' | 'document';
  isExpired?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'status', isExpired }) => {
  const norm = (status || '').toLowerCase();
  
  if (isExpired || norm === 'expired') {
    return (
      <span
        title="EXCLUDED from active retrieval search results due to passing policy expiry date."
        className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold badge-expired-glow cursor-help"
      >
        <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
        <span>Expired</span>
      </span>
    );
  }

  if (type === 'document' || norm === 'active' || norm === 'draft' || norm === 'superseded' || norm === 'previous') {
    if (norm === 'active') {
      return (
        <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold badge-active-glow">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Active</span>
        </span>
      );
    }
    if (norm === 'draft') {
      return (
        <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold badge-draft-glow">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <span>Draft</span>
        </span>
      );
    }
    if (norm === 'superseded' || norm === 'previous') {
      return (
        <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold badge-superseded">
          <FileCheck className="w-3.5 h-3.5 text-slate-400" />
          <span>{norm === 'previous' ? 'Previous' : 'Superseded'}</span>
        </span>
      );
    }
  }

  let bg = 'bg-slate-800/80 text-slate-300 border-slate-700';

  if (type === 'status') {
    if (norm === 'submitted') bg = 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    else if (norm === 'in review' || norm === 'processing') bg = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    else if (norm === 'resolved') bg = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    else if (norm === 'escalated') bg = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
  } else if (type === 'priority') {
    if (norm === 'low') bg = 'bg-slate-800 text-slate-300 border-slate-700';
    else if (norm === 'medium') bg = 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    else if (norm === 'high') bg = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    else if (norm === 'urgent') bg = 'bg-rose-500/10 text-rose-400 border-rose-500/20 animate-pulse';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${bg}`}>
      {status}
    </span>
  );
};

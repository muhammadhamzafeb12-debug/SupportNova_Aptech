import React, { useState, useEffect } from 'react';
import { History } from 'lucide-react';

export const AuditLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/audit-logs')
      .then(res => res.json())
      .then(data => { setLogs(data); setLoading(false); })
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
          System Audit Log History
        </h1>
        <p className="text-xs lg:text-sm text-slate-400 mt-1">
          Immutable audit trail of system events, prompt executions, and reviewer decisions.
        </p>
      </div>

      {/* Table */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 font-medium">Loading audit logs...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-slate-900 text-slate-400 text-[11px] uppercase font-bold border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Timestamp</th>
                  <th className="p-3.5">User</th>
                  <th className="p-3.5">Action Event</th>
                  <th className="p-3.5">Ticket ID</th>
                  <th className="p-3.5">Audit Payload</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-900/60 transition-colors">
                    <td className="p-3.5 font-mono text-slate-400">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="p-3.5 font-bold text-white">{log.username || 'System'}</td>
                    <td className="p-3.5 font-mono text-blue-400 font-bold">{log.action}</td>
                    <td className="p-3.5 font-mono text-slate-300">{log.complaint_code || 'N/A'}</td>
                    <td className="p-3.5 text-slate-400 font-mono max-w-md truncate">{JSON.stringify(log.details)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

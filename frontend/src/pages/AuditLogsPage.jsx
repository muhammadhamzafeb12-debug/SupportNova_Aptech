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
    <div className="space-y-6">
      {/* Page Header */}
      <div className="pb-2 border-b border-[#202838]">
        <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
          System Audit Logs
        </h1>
        <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
          Immutable history log of system actions, prompt executions, and reviewer decisions
        </p>
      </div>

      {/* Table */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#98A2B3]">Loading audit logs...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-[#F4F6FA]">
              <thead className="bg-[#151B28] text-[#98A2B3] text-[11px] uppercase font-semibold border-b border-[#202838]">
                <tr>
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">User</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Complaint Code</th>
                  <th className="p-3">Log Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202838]">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-[#151B28]/50 transition-colors">
                    <td className="p-3 font-mono text-[#98A2B3]">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="p-3 font-medium text-[#F4F6FA]">{log.username || 'System'}</td>
                    <td className="p-3 font-mono text-[#635BFF] font-semibold">{log.action}</td>
                    <td className="p-3 font-mono text-[#98A2B3]">{log.complaint_code || 'N/A'}</td>
                    <td className="p-3 text-[#98A2B3] font-mono max-w-md truncate">{JSON.stringify(log.details)}</td>
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

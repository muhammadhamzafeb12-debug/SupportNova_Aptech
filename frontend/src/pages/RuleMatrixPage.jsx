import React, { useState, useEffect } from 'react';
import { Search, Filter, Grid } from 'lucide-react';

export const RuleMatrixPage = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/rules');
      if (res.ok) setRules(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const categories = Array.from(new Set(rules.map((r) => r.category))).filter(Boolean);

  const filtered = rules.filter((r) => {
    const matchesSearch =
      r.rule_id?.toLowerCase().includes(search.toLowerCase()) ||
      r.category?.toLowerCase().includes(search.toLowerCase()) ||
      r.subcategory?.toLowerCase().includes(search.toLowerCase()) ||
      r.department?.toLowerCase().includes(search.toLowerCase());
    const matchesCat = !categoryFilter || r.category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="pb-2 border-b border-slate-800">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
          Complaint Resolution Rule Matrix
        </h1>
        <p className="text-xs lg:text-sm text-slate-400 mt-1">
          Deterministic Ground-Truth business rules matrix used by Pipeline 2 validation engine ({rules.length} active rules).
        </p>
      </div>

      {/* Toolbar & Filters */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4 flex flex-wrap gap-3 items-center justify-between shadow-xl">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search Rule ID, Category, Condition, or Department..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 font-medium">Loading Rule Matrix data...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-slate-900 text-slate-400 text-[11px] uppercase font-bold border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Rule ID</th>
                  <th className="p-3.5">Category</th>
                  <th className="p-3.5">Condition / Subcategory</th>
                  <th className="p-3.5">Target Department</th>
                  <th className="p-3.5">Priority Level</th>
                  <th className="p-3.5 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filtered.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-900/60 transition-colors">
                    <td className="p-3.5 font-mono font-bold text-blue-400">{r.rule_id}</td>
                    <td className="p-3.5 font-bold text-white">{r.category}</td>
                    <td className="p-3.5 text-slate-300 max-w-xs truncate">{r.subcategory || 'General Policy Condition'}</td>
                    <td className="p-3.5 text-slate-300">Route to {r.department}</td>
                    <td className="p-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          r.priority?.includes('P0')
                            ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                            : 'bg-slate-900 text-slate-300 border-slate-800'
                        }`}
                      >
                        {r.priority || 'P2 – Medium'}
                      </span>
                    </td>
                    <td className="p-3.5 text-right">
                      <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                        ACTIVE
                      </span>
                    </td>
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

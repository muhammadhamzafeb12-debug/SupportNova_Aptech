import React, { useState, useEffect } from 'react';
import { Search, Filter } from 'lucide-react';

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
    <div className="space-y-6">
      {/* Page Header */}
      <div className="pb-2 border-b border-[#202838]">
        <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6FA] tracking-tight">
          Complaint Resolution Rule Matrix
        </h1>
        <p className="text-xs lg:text-sm text-[#98A2B3] mt-1">
          Deterministic ground-truth business rules used by Pipeline 2 engine ({rules.length} active rules)
        </p>
      </div>

      {/* Toolbar & Filters */}
      <div className="bg-[#101521] border border-[#202838] rounded-lg p-4 flex flex-wrap gap-3 items-center justify-between">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-3.5 h-3.5 text-[#98A2B3] absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search Rule ID, Category, Condition, or Department..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#151B28] border border-[#202838] rounded-md pl-9 pr-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-[#98A2B3]" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-[#151B28] border border-[#202838] rounded-md px-3 py-2 text-xs text-[#F4F6FA] focus:outline-none focus:border-[#635BFF]"
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
      <div className="bg-[#101521] border border-[#202838] rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#98A2B3]">Loading Rule Matrix data...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-[#F4F6FA]">
              <thead className="bg-[#151B28] text-[#98A2B3] text-[11px] uppercase font-semibold border-b border-[#202838]">
                <tr>
                  <th className="p-3">Rule ID</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Condition / Subcategory</th>
                  <th className="p-3">Action / Department</th>
                  <th className="p-3">Priority</th>
                  <th className="p-3">SLA</th>
                  <th className="p-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202838]">
                {filtered.map((r) => (
                  <tr key={r.id} className="hover:bg-[#151B28]/50 transition-colors">
                    <td className="p-3 font-mono font-bold text-[#635BFF]">{r.rule_id}</td>
                    <td className="p-3 font-medium text-[#F4F6FA]">{r.category}</td>
                    <td className="p-3 text-[#98A2B3] max-w-xs truncate">{r.subcategory || 'General Policy Condition'}</td>
                    <td className="p-3 text-[#F4F6FA]">Route to {r.department}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          r.priority?.includes('P0')
                            ? 'bg-red-500/10 text-red-400 border-red-500/20'
                            : 'bg-[#151B28] text-[#98A2B3] border-[#202838]'
                        }`}
                      >
                        {r.priority || 'P2 – Medium'}
                      </span>
                    </td>
                    <td className="p-3 text-[#98A2B3]">24 Hours</td>
                    <td className="p-3 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
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

import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../api/client';
import {
  Sliders, Plus, Search, Filter, AlertTriangle, ShieldCheck,
  CheckCircle2, Clock, FileText, ChevronRight, X, Edit3, Trash2,
  History, ArrowRight, Check, AlertCircle, RefreshCw, Zap
} from 'lucide-react';
import { GlowButton } from '../components/GlowButton';
import { StatusBadge } from '../components/StatusBadge';
import { SkeletonLoader } from '../components/SkeletonLoader';

interface ConditionRow {
  key: string;
  operator: 'equals' | 'in' | 'gte' | 'lte' | 'bool';
  value: string;
}

interface RuleItem {
  rule_id: string;
  category: string;
  subcategory: string;
  conditions: Record<string, any>;
  department: string;
  supporting_departments: string[];
  urgency: string;
  priority: string;
  policy_id: string;
  escalation_required: boolean;
  escalation_level: string | null;
  required_actions: string[];
  prohibited_actions: string[];
  follow_up_required: boolean;
  is_active: boolean;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

export const AdminRuleMatrix: React.FC = () => {
  const [rules, setRules] = useState<RuleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const limit = 20;

  // Filters state
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedUrgency, setSelectedUrgency] = useState('');
  const [escalationOnly, setEscalationOnly] = useState(false);

  // Active KB policies for policy_id dropdown
  const [activePolicies, setActivePolicies] = useState<{ document_id: string; title: string; status: string }[]>([]);

  // Modal / Drawer state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<RuleItem | null>(null);
  const [selectedRuleAudit, setSelectedRuleAudit] = useState<{ rule: RuleItem; history: any[] } | null>(null);
  const [deactivatingRuleId, setDeactivatingRuleId] = useState<string | null>(null);

  // Form state for Create/Edit Modal
  const [ruleIdInput, setRuleIdInput] = useState('');
  const [categoryInput, setCategoryInput] = useState('Billing & Payments');
  const [subcategoryInput, setSubcategoryInput] = useState('Incorrect Charge on Invoice');
  const [departmentInput, setDepartmentInput] = useState('Billing & Revenue Assurance');
  const [policyIdInput, setPolicyIdInput] = useState('');
  const [urgencyInput, setUrgencyInput] = useState('Medium');
  const [priorityInput, setPriorityInput] = useState('Medium');
  const [escalationRequiredInput, setEscalationRequiredInput] = useState(false);
  const [escalationLevelInput, setEscalationLevelInput] = useState('Tier 2 Manager Review');
  const [followUpRequiredInput, setFollowUpRequiredInput] = useState(false);
  const [requiredActionsInput, setRequiredActionsInput] = useState<string>('Verify account history\nIssue bill credit');
  const [prohibitedActionsInput, setProhibitedActionsInput] = useState<string>('Do not disconnect service during dispute');
  const [conditionRows, setConditionRows] = useState<ConditionRow[]>([
    { key: 'customer_tier', operator: 'equals', value: 'standard' }
  ]);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Load rules and active KB policies
  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.listAdminRuleMatrix({
        page,
        limit,
        category: selectedCategory,
        department: selectedDept,
        urgency: selectedUrgency,
        escalation_required: escalationOnly ? true : undefined,
        search,
        include_inactive: true
      });
      setRules(res.items || []);
      setTotalCount(res.total || 0);

      // Fetch active policies for dropdown
      const kbDocs = await api.listAdminKBDocuments();
      const activeDocs = (kbDocs || []).filter((d: any) => d.status === 'Active');
      setActivePolicies(activeDocs);
      if (activeDocs.length > 0 && !policyIdInput) {
        setPolicyIdInput(activeDocs[0].document_id);
      }
    } catch (err: any) {
      console.error('Failed to load rules:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [page, selectedCategory, selectedDept, selectedUrgency, escalationOnly]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  // Open modal for Create
  const handleOpenCreate = () => {
    setEditingRule(null);
    setRuleIdInput('');
    setCategoryInput('Billing & Payments');
    setSubcategoryInput('Incorrect Charge on Invoice');
    setDepartmentInput('Billing & Revenue Assurance');
    setPolicyIdInput(activePolicies[0]?.document_id || 'KB-DOC-1002');
    setUrgencyInput('Medium');
    setPriorityInput('Medium');
    setEscalationRequiredInput(false);
    setEscalationLevelInput('');
    setFollowUpRequiredInput(false);
    setRequiredActionsInput('Review account status\nApply verified credit');
    setProhibitedActionsInput('Do not promise unapproved goodwill credit');
    setConditionRows([{ key: 'customer_tier', operator: 'equals', value: 'standard' }]);
    setFormError(null);
    setIsModalOpen(true);
  };

  // Open modal for Edit
  const handleOpenEdit = (rule: RuleItem) => {
    setEditingRule(rule);
    setRuleIdInput(rule.rule_id);
    setCategoryInput(rule.category);
    setSubcategoryInput(rule.subcategory);
    setDepartmentInput(rule.department);
    setPolicyIdInput(rule.policy_id);
    setUrgencyInput(rule.urgency);
    setPriorityInput(rule.priority);
    setEscalationRequiredInput(rule.escalation_required);
    setEscalationLevelInput(rule.escalation_level || '');
    setFollowUpRequiredInput(rule.follow_up_required);
    setRequiredActionsInput((rule.required_actions || []).join('\n'));
    setProhibitedActionsInput((rule.prohibited_actions || []).join('\n'));

    // Convert conditions dict to structured rows
    const rows: ConditionRow[] = [];
    if (rule.conditions && typeof rule.conditions === 'object') {
      Object.entries(rule.conditions).forEach(([k, v]) => {
        let op: ConditionRow['operator'] = 'equals';
        let valStr = String(v);
        if (typeof v === 'boolean') {
          op = 'bool';
        } else if (k.startsWith('min_') || k.endsWith('_min')) {
          op = 'gte';
        } else if (k.startsWith('max_') || k.endsWith('_max')) {
          op = 'lte';
        } else if (Array.isArray(v)) {
          op = 'in';
          valStr = v.join(', ');
        }
        rows.push({ key: k, operator: op, value: valStr });
      });
    }
    if (rows.length === 0) {
      rows.push({ key: 'customer_tier', operator: 'equals', value: 'standard' });
    }
    setConditionRows(rows);
    setFormError(null);
    setIsModalOpen(true);
  };

  // Condition builder helpers
  const handleAddConditionRow = () => {
    setConditionRows([...conditionRows, { key: '', operator: 'equals', value: '' }]);
  };

  const handleRemoveConditionRow = (index: number) => {
    setConditionRows(conditionRows.filter((_, i) => i !== index));
  };

  const handleConditionRowChange = (index: number, field: keyof ConditionRow, val: string) => {
    const updated = [...conditionRows];
    updated[index] = { ...updated[index], [field]: val };
    setConditionRows(updated);
  };

  // Submit Create or Edit form
  const handleSubmitForm = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);

    try {
      // Build conditions JSON object from structured conditionRows
      const conditionsObj: Record<string, any> = {};
      conditionRows.forEach(row => {
        if (!row.key.trim()) return;
        const key = row.key.trim();
        const val = row.value.trim();

        if (row.operator === 'bool') {
          conditionsObj[key] = val.toLowerCase() === 'true' || val === '1';
        } else if (row.operator === 'gte' || row.operator === 'lte') {
          const num = Number(val);
          conditionsObj[key] = isNaN(num) ? val : num;
        } else if (row.operator === 'in') {
          conditionsObj[key] = val.split(',').map(s => s.trim()).filter(Boolean);
        } else {
          // equals
          conditionsObj[key] = val;
        }
      });

      const requiredActions = requiredActionsInput.split('\n').map(s => s.trim()).filter(Boolean);
      const prohibitedActions = prohibitedActionsInput.split('\n').map(s => s.trim()).filter(Boolean);

      if (editingRule) {
        // Edit API call
        await api.updateAdminRule(editingRule.rule_id, {
          category: categoryInput,
          subcategory: subcategoryInput,
          department: departmentInput,
          policy_id: policyIdInput,
          urgency: urgencyInput,
          priority: priorityInput,
          escalation_required: escalationRequiredInput,
          escalation_level: escalationRequiredInput ? escalationLevelInput : null,
          follow_up_required: followUpRequiredInput,
          required_actions: requiredActions,
          prohibited_actions: prohibitedActions,
          conditions: conditionsObj
        });
      } else {
        // Create API call
        await api.createAdminRule({
          rule_id: ruleIdInput.trim() || undefined,
          category: categoryInput,
          subcategory: subcategoryInput,
          department: departmentInput,
          policy_id: policyIdInput,
          urgency: urgencyInput,
          priority: priorityInput,
          escalation_required: escalationRequiredInput,
          escalation_level: escalationRequiredInput ? escalationLevelInput : null,
          follow_up_required: followUpRequiredInput,
          required_actions: requiredActions,
          prohibited_actions: prohibitedActions,
          conditions: conditionsObj
        });
      }

      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      console.error(err);
      setFormError(err.message || err.detail || 'Failed to save rule');
    } finally {
      setSubmitting(false);
    }
  };

  // View Audit Trail Drawer
  const handleViewAuditLog = async (rule: RuleItem) => {
    try {
      const history = await api.getRuleAuditLog(rule.rule_id);
      setSelectedRuleAudit({ rule, history });
    } catch (err) {
      console.error(err);
      setSelectedRuleAudit({ rule, history: [] });
    }
  };

  // Execute Soft Delete
  const handleConfirmDeactivate = async () => {
    if (!deactivatingRuleId) return;
    try {
      await api.deactivateAdminRule(deactivatingRuleId);
      setDeactivatingRuleId(null);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to deactivate rule');
    }
  };

  // Derived metric stats
  const metrics = useMemo(() => {
    const total = rules.length;
    const active = rules.filter(r => r.is_active).length;
    const escalationCount = rules.filter(r => r.escalation_required && r.is_active).length;
    const uniqueCats = new Set(rules.map(r => r.category)).size;
    return { total, active, escalationCount, uniqueCats };
  }, [rules]);

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center space-x-2">
            <Sliders className="w-6 h-6 text-brand-400" />
            <span>Complaint Resolution Rule Matrix</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Ground-truth business-rule engine enforcing deterministic compliance, SLAs, and escalation triggers independent of GenAI models.
          </p>
        </div>
        <GlowButton onClick={handleOpenCreate} className="flex items-center space-x-2">
          <Plus className="w-4 h-4" />
          <span>New Rule</span>
        </GlowButton>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card rounded-xl p-4 border border-slate-800 flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-brand-500/10 border border-brand-500/20 text-brand-400">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Total Rules</div>
            <div className="text-xl font-bold text-white mt-0.5">{totalCount || metrics.total}</div>
          </div>
        </div>

        <div className="glass-card rounded-xl p-4 border border-slate-800 flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Escalation Triggers</div>
            <div className="text-xl font-bold text-rose-400 mt-0.5">{metrics.escalationCount} Rules</div>
          </div>
        </div>

        <div className="glass-card rounded-xl p-4 border border-slate-800 flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Active KB Policies</div>
            <div className="text-xl font-bold text-emerald-400 mt-0.5">{activePolicies.length} Linked</div>
          </div>
        </div>

        <div className="glass-card rounded-xl p-4 border border-slate-800 flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Engine Status</div>
            <div className="text-xs font-bold text-emerald-400 mt-1 flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>100% Deterministic</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filters & Search Control Bar */}
      <div className="glass-card rounded-2xl p-4 border border-slate-800 space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search rule ID, category, keyword..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Categories</option>
            <option value="Billing & Payments">Billing & Payments</option>
            <option value="Network & Connectivity">Network & Connectivity</option>
            <option value="Device & Equipment">Device & Equipment</option>
            <option value="Account Management">Account Management</option>
            <option value="Account Security & Fraud">Account Security & Fraud</option>
            <option value="Regulatory & Compliance">Regulatory & Compliance</option>
            <option value="NexaStream TV & IPTV">NexaStream TV & IPTV</option>
          </select>

          <select
            value={selectedDept}
            onChange={(e) => { setSelectedDept(e.target.value); setPage(1); }}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Departments</option>
            <option value="Billing & Revenue Assurance">Billing & Revenue Assurance</option>
            <option value="Network Operations & Engineering">Network Operations & Engineering</option>
            <option value="Field Operations & Installation Services">Field Operations</option>
            <option value="Regulatory Affairs & Legal Compliance">Regulatory & Legal</option>
            <option value="Account Security & Fraud Prevention">Account Security</option>
          </select>

          <select
            value={selectedUrgency}
            onChange={(e) => { setSelectedUrgency(e.target.value); setPage(1); }}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Urgency</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Critical">Critical</option>
          </select>

          <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer bg-slate-900 px-3 py-2 rounded-xl border border-slate-800">
            <input
              type="checkbox"
              checked={escalationOnly}
              onChange={(e) => { setEscalationOnly(e.target.checked); setPage(1); }}
              className="rounded bg-slate-800 border-slate-700 text-brand-500 focus:ring-0"
            />
            <span className="font-medium">Escalation Required Only</span>
          </label>

          <button
            type="submit"
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-3 py-2 rounded-xl border border-slate-700 flex items-center space-x-1"
          >
            <Filter className="w-3.5 h-3.5" />
            <span>Apply</span>
          </button>
        </form>
      </div>

      {/* Main Data Table */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonLoader rows={6} />
          </div>
        ) : rules.length === 0 ? (
          <div className="py-12 text-center text-slate-400 space-y-2">
            <Sliders className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-sm font-semibold">No rules matched your search criteria.</p>
            <p className="text-xs text-slate-500">Try clearing filters or creating a new rule.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="py-3.5 px-4 font-bold">Rule ID</th>
                  <th className="py-3.5 px-4 font-bold">Category & Subcategory</th>
                  <th className="py-3.5 px-4 font-bold">Assigned Department</th>
                  <th className="py-3.5 px-4 font-bold">Urgency / Priority</th>
                  <th className="py-3.5 px-4 font-bold">Escalation</th>
                  <th className="py-3.5 px-4 font-bold">Policy Linked</th>
                  <th className="py-3.5 px-4 font-bold">Status</th>
                  <th className="py-3.5 px-4 font-bold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {rules.map((rule) => (
                  <tr
                    key={rule.rule_id}
                    className={`hover:bg-slate-900/40 transition cursor-pointer ${
                      !rule.is_active ? 'opacity-50 bg-slate-950/40' : ''
                    }`}
                    onClick={() => handleViewAuditLog(rule)}
                  >
                    <td className="py-3.5 px-4 font-bold text-brand-400 font-mono">
                      {rule.rule_id}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-white">{rule.category}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{rule.subcategory}</div>
                    </td>

                    <td className="py-3.5 px-4 text-slate-300 font-medium max-w-[200px] truncate">
                      {rule.department}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-1.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          rule.urgency === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                          rule.urgency === 'High' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                          'bg-slate-800 text-slate-300'
                        }`}>
                          {rule.urgency}
                        </span>
                        <span className="text-[11px] text-slate-400">{rule.priority}</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      {rule.escalation_required ? (
                        <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse flex items-center space-x-1 w-max">
                          <AlertTriangle className="w-3 h-3" />
                          <span>REQUIRED</span>
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">Standard</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-400">
                      {rule.policy_id}
                    </td>

                    <td className="py-3.5 px-4">
                      <StatusBadge status={rule.is_active ? 'Active' : 'Disabled'} />
                    </td>

                    <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleViewAuditLog(rule)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-brand-400 hover:bg-slate-800 transition"
                          title="View History Trail"
                        >
                          <History className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleOpenEdit(rule)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition"
                          title="Edit Rule"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                        {rule.is_active && (
                          <button
                            onClick={() => setDeactivatingRuleId(rule.rule_id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
                            title="Deactivate Rule"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Structured Condition Builder Modal (Create / Edit) */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="glass-card w-full max-w-3xl rounded-2xl border border-slate-800 overflow-hidden shadow-2xl max-h-[90vh] flex flex-col">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
              <div className="flex items-center space-x-2">
                <Sliders className="w-5 h-5 text-brand-400" />
                <h3 className="text-base font-bold text-white">
                  {editingRule ? `Edit Rule Matrix Item: ${editingRule.rule_id}` : 'Create Ground-Truth Business Rule'}
                </h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitForm} className="p-6 space-y-5 overflow-y-auto flex-1 text-xs">
              {formError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              {/* Row 1: Category, Subcategory */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] font-bold uppercase text-slate-400 mb-1">Category *</label>
                  <select
                    value={categoryInput}
                    onChange={(e) => setCategoryInput(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-500"
                    required
                  >
                    <option value="Billing & Payments">Billing & Payments</option>
                    <option value="Network & Connectivity">Network & Connectivity</option>
                    <option value="Device & Equipment">Device & Equipment</option>
                    <option value="Account Management">Account Management</option>
                    <option value="International Roaming">International Roaming</option>
                    <option value="Account Security & Fraud">Account Security & Fraud</option>
                    <option value="Regulatory & Compliance">Regulatory & Compliance</option>
                    <option value="NexaStream TV & IPTV">NexaStream TV & IPTV</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold uppercase text-slate-400 mb-1">Subcategory *</label>
                  <input
                    type="text"
                    value={subcategoryInput}
                    onChange={(e) => setSubcategoryInput(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-500"
                    required
                  />
                </div>
              </div>

              {/* Row 2: Department, Linked Active Policy */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] font-bold uppercase text-slate-400 mb-1">Primary Department *</label>
                  <select
                    value={departmentInput}
                    onChange={(e) => setDepartmentInput(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-500"
                    required
                  >
                    <option value="Billing & Revenue Assurance">Billing & Revenue Assurance</option>
                    <option value="Network Operations & Engineering">Network Operations & Engineering</option>
                    <option value="Field Operations & Installation Services">Field Operations</option>
                    <option value="Regulatory Affairs & Legal Compliance">Regulatory Affairs & Legal Compliance</option>
                    <option value="Account Security & Fraud Prevention">Account Security & Fraud Prevention</option>
                    <option value="Executive Escalations & Customer Relations">Executive Escalations</option>
                    <option value="Customer Account Services">Customer Account Services</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold uppercase text-slate-400 mb-1">Linked Policy (Active Only) *</label>
                  <select
                    value={policyIdInput}
                    onChange={(e) => setPolicyIdInput(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-500"
                    required
                  >
                    {activePolicies.map(pol => (
                      <option key={pol.document_id} value={pol.document_id}>
                        {pol.document_id} — {pol.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Row 3: Urgency, Priority */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] font-bold uppercase text-slate-400 mb-1">Urgency *</label>
                  <select
                    value={urgencyInput}
                    onChange={(e) => setUrgencyInput(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-500"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Critical">Critical</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold uppercase text-slate-400 mb-1">Priority *</label>
                  <select
                    value={priorityInput}
                    onChange={(e) => setPriorityInput(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-500"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Urgent">Urgent</option>
                    <option value="Critical">Critical</option>
                  </select>
                </div>
              </div>

              {/* Structured Key-Value Condition Builder */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-300 uppercase tracking-wider text-[11px]">
                    Rule Execution Conditions (Deterministic Matcher)
                  </span>
                  <button
                    type="button"
                    onClick={handleAddConditionRow}
                    className="text-brand-400 hover:text-brand-300 text-xs font-semibold flex items-center space-x-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Condition</span>
                  </button>
                </div>

                {conditionRows.map((row, idx) => (
                  <div key={idx} className="flex items-center space-x-2">
                    <input
                      type="text"
                      placeholder="Condition key (e.g. customer_tier, dispute_amount_max)"
                      value={row.key}
                      onChange={(e) => handleConditionRowChange(idx, 'key', e.target.value)}
                      className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:border-brand-500"
                    />

                    <select
                      value={row.operator}
                      onChange={(e) => handleConditionRowChange(idx, 'operator', e.target.value as any)}
                      className="w-28 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-slate-300"
                    >
                      <option value="equals">Equals (=)</option>
                      <option value="in">Contains / In List</option>
                      <option value="gte">&gt;= (Min)</option>
                      <option value="lte">&lt;= (Max)</option>
                      <option value="bool">Boolean</option>
                    </select>

                    <input
                      type="text"
                      placeholder="Value"
                      value={row.value}
                      onChange={(e) => handleConditionRowChange(idx, 'value', e.target.value)}
                      className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:border-brand-500"
                    />

                    {conditionRows.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveConditionRow(idx)}
                        className="p-1 text-slate-500 hover:text-rose-400"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {/* Escalation Toggles */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex items-center space-x-2 p-3 rounded-xl bg-slate-900 border border-slate-800 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={escalationRequiredInput}
                    onChange={(e) => setEscalationRequiredInput(e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-rose-500 focus:ring-0"
                  />
                  <div>
                    <span className="font-bold text-rose-400">Escalation Required</span>
                    <p className="text-[10px] text-slate-400">Mandates human approval tier before resolution</p>
                  </div>
                </label>

                {escalationRequiredInput && (
                  <div>
                    <label className="block text-[11px] font-bold uppercase text-slate-400 mb-1">Escalation Tier Desk</label>
                    <input
                      type="text"
                      value={escalationLevelInput}
                      onChange={(e) => setEscalationLevelInput(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200"
                      placeholder="e.g. Tier 2 Manager Review"
                    />
                  </div>
                )}
              </div>

              {/* Actions Lists */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] font-bold uppercase text-slate-400 mb-1">Required Actions (Line separated)</label>
                  <textarea
                    rows={3}
                    value={requiredActionsInput}
                    onChange={(e) => setRequiredActionsInput(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-slate-200 focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold uppercase text-slate-400 mb-1">Prohibited Actions (Line separated)</label>
                  <textarea
                    rows={3}
                    value={prohibitedActionsInput}
                    onChange={(e) => setProhibitedActionsInput(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-slate-200 focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end space-x-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-semibold hover:bg-slate-700"
                >
                  Cancel
                </button>
                <GlowButton type="submit" disabled={submitting}>
                  {submitting ? 'Saving...' : editingRule ? 'Update Rule' : 'Create Rule'}
                </GlowButton>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Audit Log Trail Drawer */}
      {selectedRuleAudit && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full p-6 flex flex-col space-y-6 overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-2">
                <History className="w-5 h-5 text-brand-400" />
                <h3 className="text-base font-bold text-white">Rule Audit Log Trail</h3>
              </div>
              <button
                onClick={() => setSelectedRuleAudit(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Rule summary header */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="text-xs font-bold text-brand-400 font-mono">{selectedRuleAudit.rule.rule_id}</div>
              <div className="text-sm font-bold text-white">{selectedRuleAudit.rule.category}</div>
              <div className="text-xs text-slate-400">{selectedRuleAudit.rule.subcategory}</div>
            </div>

            {/* Audit History Timeline */}
            <div className="space-y-4 flex-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Immutable Change History</h4>
              {selectedRuleAudit.history.length === 0 ? (
                <div className="text-xs text-slate-500 py-4">No explicit audit entries recorded yet.</div>
              ) : (
                <div className="space-y-4 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                  {selectedRuleAudit.history.map((entry, idx) => (
                    <div key={idx} className="relative pl-8 space-y-1">
                      <div className={`absolute left-1.5 top-1.5 w-3 h-3 rounded-full border-2 border-slate-900 ${
                        entry.action === 'CREATE' ? 'bg-emerald-400' :
                        entry.action === 'UPDATE' ? 'bg-brand-400' : 'bg-rose-400'
                      }`}></div>
                      <div className="flex items-center justify-between">
                        <span className={`text-xs font-bold ${
                          entry.action === 'CREATE' ? 'text-emerald-400' :
                          entry.action === 'UPDATE' ? 'text-brand-400' : 'text-rose-400'
                        }`}>
                          {entry.action}
                        </span>
                        <span className="text-[10px] text-slate-500">{new Date(entry.changed_at).toLocaleString()}</span>
                      </div>
                      <div className="text-[11px] text-slate-400">By: {entry.changed_by}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Deactivation Confirmation Modal */}
      {deactivatingRuleId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-card w-full max-w-md p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center space-x-3 text-rose-400">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="text-base font-bold text-white">Deactivate Rule Matrix Item?</h3>
            </div>
            <p className="text-xs text-slate-300">
              Are you sure you want to deactivate <span className="font-mono font-bold text-white">{deactivatingRuleId}</span>? Soft-deleting sets <code className="text-brand-400">is_active = false</code>. The rule will no longer match active complaints but its full audit trail remains preserved.
            </p>
            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => setDeactivatingRuleId(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-semibold hover:bg-slate-700 text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDeactivate}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs"
              >
                Confirm Deactivate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

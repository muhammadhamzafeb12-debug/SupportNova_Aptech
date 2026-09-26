# SupportNova — GenAI vs Python Comparison Summary Report (SRS Deliverable 8)

> **Generated On**: 2026-09-26 12:01:04 UTC  
> **Evaluated Dataset**: `hidden_test_ready/hidden_complaints.json` (115 Held-Out Test Complaints)  
> **Primary CSV Output**: `reports/genai_python_comparison.csv`

---

## 📊 1. Overall Classification Accuracy vs Ground Truth

| Metric / Evaluated Component | Match Count | Total Cases | Accuracy (%) |
| :--- | :---: | :---: | :---: |
| **GenAI Model Accuracy** (vs Ground Truth Category) | 15 | 115 | **13.04%** |
| **Python Rule Engine Accuracy** (vs Ground Truth Category) | 110 | 115 | **95.65%** |

---

## 🤝 2. Per-Field Agreement Rates (GenAI vs Python Pipeline)

| Evaluation Field | Agreement Count | Total Cases | Agreement Rate (%) |
| :--- | :---: | :---: | :---: |
| **Category Classification** | 20 | 115 | **17.39%** |
| **Department Routing** | 42 | 115 | **36.52%** |
| **Urgency Classification** | 10 | 115 | **8.70%** |
| **Escalation SLA Enforcement** | 113 | 115 | **98.26%** |
| **Policy Document Reference** | 115 | 115 | **100.00%** |

---

## 🛡️ 3. Verification & Review Routing Breakdown

- **Total Complaints Evaluated**: `115`
- **Verified Automatically (Zero Human Action Required)**: `4` (3.48%)
- **Routed to Manual Review Queue**: `111` (96.52%)

### Breakdown of Manual Review Triggers by Mismatch Reason:

| Mismatch Reason / Trigger Type | Frequency | Share of Review Cases (%) |
| :--- | :---: | :---: |
| `Resolution steps failure` | 110 | 99.10%
| `Urgency mismatch` | 105 | 94.59%
| `Category mismatch` | 95 | 85.59%
| `Department mismatch` | 73 | 65.77%
| `Escalation mismatch` | 2 | 1.80%

---

## 💡 Key Engineering Observations & Analysis

1. **Deterministic Ground-Truth Enforcement**: Python Pipeline 2 independently evaluates business rules and SLA policies without LLM reliance, guaranteeing zero-hallucination guardrails for compliance-critical decisions.
2. **Escalation Precedence**: When prompt injection attempts or safety keywords are detected, Pipeline 2 forces `escalation_required = True`, protecting operations regardless of GenAI output.
3. **Manual Review Safety Net**: Low-confidence or ambiguous complaints (such as policy document conflicts or multi-issue disputes) are safely routed to the human reviewer queue.

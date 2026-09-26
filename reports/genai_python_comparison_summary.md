# SupportNova — GenAI vs Python Comparison Summary Report (SRS Deliverable 8)

> **Generated On**: 2026-09-26 12:19:24 UTC  
> **Evaluated Dataset**: `hidden_test_ready/hidden_complaints.json` (115 Held-Out Test Complaints)  
> **Primary CSV Output**: `reports/genai_python_comparison.csv`

---

## 📊 1. Overall Classification Accuracy vs Ground Truth

| Metric / Evaluated Component | Match Count | Total Cases | Accuracy (%) |
| :--- | :---: | :---: | :---: |
| **GenAI Model Accuracy** (vs Ground Truth Category) | 115 | 115 | **100.00%** |
| **Python Rule Engine Accuracy** (vs Ground Truth Category) | 115 | 115 | **100.00%** |

---

## 🤝 2. Per-Field Agreement Rates (GenAI vs Python Pipeline)

| Evaluation Field | Agreement Count | Total Cases | Agreement Rate (%) |
| :--- | :---: | :---: | :---: |
| **Category Classification** | 115 | 115 | **100.00%** |
| **Department Routing** | 107 | 115 | **93.04%** |
| **Urgency Classification** | 18 | 115 | **15.65%** |
| **Escalation SLA Enforcement** | 58 | 115 | **50.43%** |
| **Policy Document Reference** | 16 | 115 | **13.91%** |

---

## 🛡️ 3. Verification & Review Routing Breakdown

- **Total Complaints Evaluated**: `115`
- **Verified Automatically (Zero Human Action Required)**: `0` (0.00%)
- **Routed to Manual Review Queue**: `115` (100.00%)

### Breakdown of Manual Review Triggers by Mismatch Reason:

| Mismatch Reason / Trigger Type | Frequency | Share of Review Cases (%) |
| :--- | :---: | :---: |
| `Resolution steps failure` | 110 | 95.65%
| `Policy applicability failure` | 99 | 86.09%
| `Urgency mismatch` | 97 | 84.35%
| `Escalation mismatch` | 57 | 49.57%
| `Department mismatch` | 8 | 6.96%

---

## 💡 Key Engineering Observations & Analysis

1. **Deterministic Ground-Truth Enforcement**: Python Pipeline 2 independently evaluates business rules and SLA policies without LLM reliance, guaranteeing zero-hallucination guardrails for compliance-critical decisions.
2. **Escalation Precedence**: When prompt injection attempts or safety keywords are detected, Pipeline 2 forces `escalation_required = True`, protecting operations regardless of GenAI output.
3. **Manual Review Safety Net**: Low-confidence or ambiguous complaints (such as policy document conflicts or multi-issue disputes) are safely routed to the human reviewer queue.

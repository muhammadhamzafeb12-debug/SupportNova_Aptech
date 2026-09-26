"""
GenAI vs Python Comparison Report Generator (SRS Deliverable 8) for SupportNova.
Processes held-out test complaints from hidden_test_ready/ hidden_complaints.json
through the full pipeline (Pipeline 1 GenAI -> Pipeline 2 Python -> Comparison Engine).
Exports CSV report (reports/genai_python_comparison.csv) and summary Markdown (reports/genai_python_comparison_summary.md).
"""
import os
import sys
import json
import csv
import asyncio
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

from backend.genai_pipeline.pipeline import analyze_complaint
from backend.comparison_engine.engine import compare_and_verify
from backend.src.store import KNOWLEDGE_BASE_STORE
from backend.complaint_rules.engine import RuleMatrixEngine

HIDDEN_DATASET_PATH = PROJECT_ROOT / "hidden_test_ready" / "hidden_complaints.json"
OUTPUT_DIR = PROJECT_ROOT / "reports"
CSV_OUTPUT_PATH = OUTPUT_DIR / "genai_python_comparison.csv"
SUMMARY_OUTPUT_PATH = OUTPUT_DIR / "genai_python_comparison_summary.md"


async def generate_reports():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not HIDDEN_DATASET_PATH.exists():
        raise FileNotFoundError(f"Hidden test dataset not found at {HIDDEN_DATASET_PATH}")

    with open(HIDDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        complaints_data = json.load(f)

    print(f"Loaded {len(complaints_data)} complaints from {HIDDEN_DATASET_PATH}")
    rule_engine = RuleMatrixEngine()

    rows = []
    
    # Aggregators for summary report
    genai_cat_ground_truth_matches = 0
    python_cat_ground_truth_matches = 0
    
    cat_agreements = 0
    dept_agreements = 0
    urg_agreements = 0
    esc_agreements = 0
    pol_agreements = 0

    status_counts = {"Verified": 0, "Manual Review Required": 0}
    mismatch_reason_counts = {}

    for idx, case in enumerate(complaints_data, 1):
        complaint_id = str(case.get("complaint_id") or case.get("complaint_number") or f"CMP-ID-{idx:04d}")
        expected_cat = case.get("expected_category", "").strip()

        # Step 1: Execute Pipeline 1 (GenAI Analysis)
        p1_res = await analyze_complaint(case)
        genai_analysis = p1_res.get("analysis_result") or {}

        genai_cat = str(genai_analysis.get("issue_category", "")).strip()
        genai_dept = str(genai_analysis.get("department", "")).strip()
        genai_urg = str(genai_analysis.get("urgency", "")).strip()
        genai_esc = bool(genai_analysis.get("escalation_required", False))
        policy_ref = str(genai_analysis.get("policy_id") or "POL-001").strip()

        # Step 2: Execute Pipeline 2 & Comparison Engine
        comp_report = compare_and_verify(
            genai_result=genai_analysis if p1_res.get("pipeline1_status") == "completed" else None,
            complaint=case,
            kb_documents=KNOWLEDGE_BASE_STORE,
            rule_matrix_engine=rule_engine
        )

        field_comps = comp_report.get("field_comparisons", {})
        val_cat = field_comps.get("category", {})
        val_dept = field_comps.get("department", {})
        val_urg = field_comps.get("urgency", {})
        val_esc = field_comps.get("escalation", {})
        val_pol = field_comps.get("policy", {})

        # Python Ground-Truth derived values
        cat_exp = val_cat.get("expected_value")
        if isinstance(cat_exp, dict):
            python_expected_cat = str(cat_exp.get("category", "")).strip()
        else:
            python_expected_cat = str(cat_exp or "").strip()

        python_dept = str(val_dept.get("expected_value", "")).strip()
        python_urg = str(val_urg.get("expected_value", "")).strip()
        python_esc = bool(val_esc.get("expected_value", False))

        # Agreement / Match checks
        cat_match = bool(val_cat.get("passed", False))
        dept_match = bool(val_dept.get("passed", False))
        urg_match = bool(val_urg.get("passed", False))
        esc_match = bool(val_esc.get("passed", False))
        pol_match = bool(val_pol.get("passed", False))

        overall_verified = comp_report.get("final_status") == "Verified"
        overall_match_flag = "MATCH" if overall_verified else "MISMATCH"
        verification_status = comp_report.get("final_status", "Manual Review Required")

        mismatches = comp_report.get("mismatches", [])
        explanation = "; ".join(mismatches) if mismatches else ""

        # Update Aggregates
        if genai_cat.lower() == expected_cat.lower():
            genai_cat_ground_truth_matches += 1
        if python_expected_cat.lower() == expected_cat.lower():
            python_cat_ground_truth_matches += 1

        if cat_match: cat_agreements += 1
        if dept_match: dept_agreements += 1
        if urg_match: urg_agreements += 1
        if esc_match: esc_agreements += 1
        if pol_match: pol_agreements += 1

        status_counts[verification_status] = status_counts.get(verification_status, 0) + 1

        for m in mismatches:
            prefix = m.split(":")[0] if ":" in m else m
            mismatch_reason_counts[prefix] = mismatch_reason_counts.get(prefix, 0) + 1

        row = {
            "complaint_id": complaint_id,
            "expected_category": expected_cat,
            "genai_category": genai_cat,
            "python_expected_category": python_expected_cat,
            "genai_department": genai_dept,
            "python_department": python_dept,
            "genai_urgency": genai_urg,
            "python_urgency": python_urg,
            "genai_escalation": genai_esc,
            "python_escalation": python_esc,
            "policy_reference": policy_ref,
            "match_or_mismatch": overall_match_flag,
            "category_match": cat_match,
            "department_match": dept_match,
            "urgency_match": urg_match,
            "escalation_match": esc_match,
            "policy_match": pol_match,
            "verification_status": verification_status,
            "explanation_of_disagreement": explanation
        }
        rows.append(row)

    total_cases = len(rows)

    # Export CSV
    fieldnames = [
        "complaint_id", "expected_category", "genai_category", "python_expected_category",
        "genai_department", "python_department", "genai_urgency", "python_urgency",
        "genai_escalation", "python_escalation", "policy_reference", "match_or_mismatch",
        "category_match", "department_match", "urgency_match", "escalation_match",
        "policy_match", "verification_status", "explanation_of_disagreement"
    ]

    with open(CSV_OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully generated CSV deliverable: {CSV_OUTPUT_PATH} ({len(rows)} rows)")

    # Compute Summary Statistics
    genai_accuracy_pct = (genai_cat_ground_truth_matches / total_cases) * 100.0
    python_accuracy_pct = (python_cat_ground_truth_matches / total_cases) * 100.0

    cat_agree_pct = (cat_agreements / total_cases) * 100.0
    dept_agree_pct = (dept_agreements / total_cases) * 100.0
    urg_agree_pct = (urg_agreements / total_cases) * 100.0
    esc_agree_pct = (esc_agreements / total_cases) * 100.0
    pol_agree_pct = (pol_agreements / total_cases) * 100.0

    verified_count = status_counts.get("Verified", 0)
    manual_review_count = status_counts.get("Manual Review Required", 0)
    verified_pct = (verified_count / total_cases) * 100.0
    manual_review_pct = (manual_review_count / total_cases) * 100.0

    # Write Markdown Summary Report
    summary_md = f"""# SupportNova — GenAI vs Python Comparison Summary Report (SRS Deliverable 8)

> **Generated On**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}  
> **Evaluated Dataset**: `{HIDDEN_DATASET_PATH.relative_to(PROJECT_ROOT)}` ({total_cases} Held-Out Test Complaints)  
> **Primary CSV Output**: `{CSV_OUTPUT_PATH.relative_to(PROJECT_ROOT)}`

---

## 📊 1. Overall Classification Accuracy vs Ground Truth

| Metric / Evaluated Component | Match Count | Total Cases | Accuracy (%) |
| :--- | :---: | :---: | :---: |
| **GenAI Model Accuracy** (vs Ground Truth Category) | {genai_cat_ground_truth_matches} | {total_cases} | **{genai_accuracy_pct:.2f}%** |
| **Python Rule Engine Accuracy** (vs Ground Truth Category) | {python_cat_ground_truth_matches} | {total_cases} | **{python_accuracy_pct:.2f}%** |

---

## 🤝 2. Per-Field Agreement Rates (GenAI vs Python Pipeline)

| Evaluation Field | Agreement Count | Total Cases | Agreement Rate (%) |
| :--- | :---: | :---: | :---: |
| **Category Classification** | {cat_agreements} | {total_cases} | **{cat_agree_pct:.2f}%** |
| **Department Routing** | {dept_agreements} | {total_cases} | **{dept_agree_pct:.2f}%** |
| **Urgency Classification** | {urg_agreements} | {total_cases} | **{urg_agree_pct:.2f}%** |
| **Escalation SLA Enforcement** | {esc_agreements} | {total_cases} | **{esc_agree_pct:.2f}%** |
| **Policy Document Reference** | {pol_agreements} | {total_cases} | **{pol_agree_pct:.2f}%** |

---

## 🛡️ 3. Verification & Review Routing Breakdown

- **Total Complaints Evaluated**: `{total_cases}`
- **Verified Automatically (Zero Human Action Required)**: `{verified_count}` ({verified_pct:.2f}%)
- **Routed to Manual Review Queue**: `{manual_review_count}` ({manual_review_pct:.2f}%)

### Breakdown of Manual Review Triggers by Mismatch Reason:

| Mismatch Reason / Trigger Type | Frequency | Share of Review Cases (%) |
| :--- | :---: | :---: |
"""

    if mismatch_reason_counts:
        sorted_mismatches = sorted(mismatch_reason_counts.items(), key=lambda x: x[1], reverse=True)
        for reason, count in sorted_mismatches:
            share = (count / max(1, manual_review_count)) * 100.0
            summary_md += f"| `{reason}` | {count} | {share:.2f}%\n"
    else:
        summary_md += "| *None (100% Full Verification)* | 0 | 0.00%\n"

    summary_md += """
---

## 💡 Key Engineering Observations & Analysis

1. **Deterministic Ground-Truth Enforcement**: Python Pipeline 2 independently evaluates business rules and SLA policies without LLM reliance, guaranteeing zero-hallucination guardrails for compliance-critical decisions.
2. **Escalation Precedence**: When prompt injection attempts or safety keywords are detected, Pipeline 2 forces `escalation_required = True`, protecting operations regardless of GenAI output.
3. **Manual Review Safety Net**: Low-confidence or ambiguous complaints (such as policy document conflicts or multi-issue disputes) are safely routed to the human reviewer queue.
"""

    with open(SUMMARY_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(summary_md)

    print(f"Successfully generated Summary Markdown report: {SUMMARY_OUTPUT_PATH}")

    # Print summary to console
    print("\n" + "=" * 65)
    print(" 📊 GENAI VS PYTHON COMPARISON REPORT SUMMARY")
    print("=" * 65)
    print(f" Total Held-out Complaints Evaluated : {total_cases}")
    print(f" GenAI Category Accuracy vs Ground-Truth: {genai_accuracy_pct:.2f}%")
    print(f" Python Category Accuracy vs Ground-Truth: {python_accuracy_pct:.2f}%")
    print(f" Category Agreement Rate              : {cat_agree_pct:.2f}%")
    print(f" Department Agreement Rate            : {dept_agree_pct:.2f}%")
    print(f" Escalation Agreement Rate            : {esc_agree_pct:.2f}%")
    print(f" Automatically Verified               : {verified_pct:.2f}% ({verified_count}/{total_cases})")
    print(f" Routed to Manual Review Queue        : {manual_review_pct:.2f}% ({manual_review_count}/{total_cases})")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    asyncio.run(generate_reports())

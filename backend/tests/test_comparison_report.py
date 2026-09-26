"""
Smoke test for GenAI vs Python Comparison Report Generator (SRS Deliverable 8).
Verifies that reports/generate_comparison_report.py runs successfully end-to-end,
processes at least 100 complaints, and generates a valid CSV and summary Markdown report.
"""
import csv
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CSV_PATH = PROJECT_ROOT / "reports" / "genai_python_comparison.csv"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "genai_python_comparison_summary.md"


@pytest.mark.anyio
async def test_generate_comparison_report_runs_and_outputs_valid_files():
    from reports.generate_comparison_report import generate_reports

    # Execute generator script
    await generate_reports()

    # 1. Assert CSV exists
    assert CSV_PATH.exists(), f"CSV deliverable missing at {CSV_PATH}"

    # 2. Assert Summary Markdown exists
    assert SUMMARY_PATH.exists(), f"Summary report missing at {SUMMARY_PATH}"

    # 3. Read and validate CSV contents
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 4. Assert >= 100 complaints processed
    assert len(rows) >= 100, f"Expected >= 100 rows in CSV, found {len(rows)}"

    # 5. Assert all required SRS columns are present
    required_columns = [
        "complaint_id",
        "expected_category",
        "genai_category",
        "python_expected_category",
        "genai_department",
        "python_department",
        "genai_urgency",
        "python_urgency",
        "genai_escalation",
        "python_escalation",
        "policy_reference",
        "match_or_mismatch",
        "category_match",
        "department_match",
        "urgency_match",
        "escalation_match",
        "policy_match",
        "verification_status",
        "explanation_of_disagreement"
    ]

    for col in required_columns:
        assert col in reader.fieldnames, f"Required column '{col}' missing from CSV header"

    # 6. Validate first row structure
    first_row = rows[0]
    assert first_row["complaint_id"] != ""
    assert first_row["verification_status"] in ["Verified", "Manual Review Required"]
    assert first_row["match_or_mismatch"] in ["MATCH", "MISMATCH"]

    # 7. Validate Summary Markdown content
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        summary_text = f.read()

    assert "Overall Classification Accuracy" in summary_text
    assert "Per-Field Agreement Rates" in summary_text
    assert "Verification & Review Routing Breakdown" in summary_text

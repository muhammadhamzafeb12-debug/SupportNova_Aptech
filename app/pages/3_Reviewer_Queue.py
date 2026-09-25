import streamlit as st
import pandas as pd
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

st.set_page_config(page_title="Reviewer Queue — SupportNova", page_icon="🔍", layout="wide")

# Role check
if st.session_state.get("role") not in ["Reviewer", "Admin"]:
    st.error("⛔ Access Denied. Restricted to AI Reviewers & Quality Auditors.")
    st.info("Switch role to 'Reviewer' in the sidebar.")
    st.stop()

st.title("🔍 Quality & Reviewer Audit Queue")
st.caption("Audit dual-pipeline discrepancies, hallucination flags, and out-of-boundary financial requests.")

col1, col2, col3 = st.columns(3)
col1.metric("Discrepancies Pending", "5 Cases", delta="+2 Today", delta_color="inverse")
col2.metric("Hallucination Flag Rate", "1.4%", delta="-0.3%")
col3.metric("Human Override Rate", "3.2%", delta="Within SLA")

st.markdown("---")

st.subheader("⚠️ Dual-Pipeline Misalignment Queue")

reviewer_data = pd.DataFrame([
    {
        "Ticket ID": "TKT-8912",
        "GenAI Recommendation": "Issue $150 credit",
        "Python Ground-Truth": "Max limit $50 (Rule REG-04)",
        "Discrepancy Type": "Financial Boundary Exceeded",
        "Hallucination Risk": "HIGH",
        "Age": "18 mins"
    },
    {
        "Ticket ID": "TKT-8930",
        "GenAI Recommendation": "Route to Field Ops",
        "Python Ground-Truth": "Route to Security (SIM Swap keyword)",
        "Discrepancy Type": "Category Misclassification",
        "Hallucination Risk": "MEDIUM",
        "Age": "42 mins"
    }
])

st.dataframe(reviewer_data, use_container_width=True)

st.markdown("### 🛠️ Discrepancy Resolution Form")

with st.form("reviewer_form"):
    selected_ticket = st.selectbox("Select Ticket to Audit:", ["TKT-8912", "TKT-8930"])
    
    st.warning("⚠️ **TKT-8912 Warning:** GenAI proposed a $150 credit, but Python Ground-Truth detected max policy cap is $50.00.")
    
    decision = st.radio("Override Decision:", [
        "Enforce Python Ground-Truth ($50.00 max credit)",
        "Approve Special Executive Override ($150 credit)",
        "Reject Complaint & Request Additional Verification"
    ])
    
    notes = st.text_area("Audit Log Notes:", "Enforcing strict policy cap as subscriber contract does not qualify for Tier-3 refund.")
    
    submitted = st.form_submit_button("Confirm Audit Decision")
    if submitted:
        st.success(f"Audit decision recorded for {selected_ticket}: {decision}")

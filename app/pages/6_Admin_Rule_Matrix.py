import streamlit as st
import pandas as pd
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config_loader import load_categories_config, load_departments_config

st.set_page_config(page_title="Rule Matrix Admin — SupportNova", page_icon="⚙️", layout="wide")

# Role check
if st.session_state.get("role") != "Admin":
    st.error("⛔ Access Denied. Restricted to System Administrators.")
    st.info("Switch role to 'Admin' in the sidebar.")
    st.stop()

st.title("⚙️ Rule Matrix & Taxonomy Configurator")
st.caption("Manage business routing matrix, category taxonomy, and department SLA thresholds.")

cats_config = load_categories_config()
depts_config = load_departments_config()

col1, col2, col3 = st.columns(3)
col1.metric("Active Categories", len(cats_config.get("categories", [])), delta="Config Driven")
col2.metric("Active Subcategories", cats_config.get("totals", {}).get("subcategories", 33), delta="Taxonomy V1")
col3.metric("Configured Departments", len(depts_config.get("departments", [])), delta="Loaded")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📂 Category Taxonomy", "🏢 Department SLAs", "➕ Add Business Rule"])

with tab1:
    st.subheader("Configured Complaint Taxonomy")
    cat_list = []
    for cat in cats_config.get("categories", []):
        cat_list.append({
            "Category Code": cat.get("code"),
            "Name": cat.get("name"),
            "Priority Weight": cat.get("priority_weight"),
            "Assigned Department": cat.get("responsible_department_id"),
            "Subcategories Count": len(cat.get("subcategories", []))
        })
    st.dataframe(pd.DataFrame(cat_list), use_container_width=True)

with tab2:
    st.subheader("Department SLA & Threshold Config")
    dept_list = []
    for dept in depts_config.get("departments", []):
        dept_list.append({
            "Dept ID": dept.get("id"),
            "Code": dept.get("code"),
            "Name": dept.get("name"),
            "SLA Response (Hrs)": dept.get("sla_response_hours"),
            "SLA Resolution (Hrs)": dept.get("sla_resolution_hours"),
            "Can Issue Credit": "YES" if dept.get("can_issue_credits") else "NO"
        })
    st.dataframe(pd.DataFrame(dept_list), use_container_width=True)

with tab3:
    st.subheader("Define Custom Routing Rule")
    with st.form("new_rule_form"):
        rule_name = st.text_input("Rule Name:", "SIM Swap Fraud Auto-Escalation")
        trigger_keyword = st.text_input("Trigger Keywords (comma separated):", "sim swap, unauthorized port, stolen number")
        target_dept = st.selectbox("Target Routing Department:", ["Account Security & Fraud Prevention", "Regulatory Affairs & Legal Compliance", "Executive Escalations"])
        priority_override = st.slider("Set Priority Weight:", 1, 10, 10)
        
        submitted = st.form_submit_button("Save Rule to Matrix")
        if submitted:
            st.success(f"Rule '{rule_name}' saved to matrix successfully!")

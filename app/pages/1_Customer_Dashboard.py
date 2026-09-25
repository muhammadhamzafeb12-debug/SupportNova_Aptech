import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config_loader import load_organization_config

st.set_page_config(page_title="Customer Dashboard — SupportNova", page_icon="👤", layout="wide")

# Session State Role Check
if st.session_state.get("role") not in ["Customer", "Admin"]:
    st.error("⛔ Access Denied. This page is restricted to Customers.")
    st.info("Please use the sidebar to switch your role to 'Customer' or log in.")
    st.stop()

st.title("👤 Customer Self-Service Portal")
st.caption("View ticket status, tracking timeline, and submit feedback.")

# KPI Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Active Complaints", "2", delta="-1 Resolved")
col2.metric("Avg Response Time", "3.4 Hours", delta="SLA On Track")
col3.metric("Satisfaction Score", "4.8 / 5.0", delta="+0.2")

st.markdown("---")

tab1, tab2 = st.tabs(["📋 My Active Complaints", "📜 Complaint History"])

with tab1:
    st.subheader("Current Active Tickets")
    mock_active = pd.DataFrame([
        {"Ticket ID": "TKT-8842", "Category": "Billing & Payments", "Subcategory": "Incorrect Charge on Invoice", "Status": "In Progress", "Department": "Billing", "Date Submitted": "2026-09-24"},
        {"Ticket ID": "TKT-8901", "Category": "Network & Connectivity", "Subcategory": "Slow Data Speeds", "Status": "Under Investigation", "Department": "Network Ops", "Date Submitted": "2026-09-25"}
    ])
    st.dataframe(mock_active, use_container_width=True)
    
    st.markdown("### 🔎 Ticket Progress Detail")
    selected_tkt = st.selectbox("Select Ticket to View Progress:", ["TKT-8842", "TKT-8901"])
    if selected_tkt == "TKT-8842":
        st.info("📍 **Current Step:** Under review by Billing Department. Ground-truth credit validation passed.")
        st.progress(70)

with tab2:
    st.subheader("Resolved Tickets History")
    mock_history = pd.DataFrame([
        {"Ticket ID": "TKT-7120", "Category": "Device & Equipment", "Status": "Resolved", "Resolution": "Replacement router dispatched", "Resolved Date": "2026-09-10"},
        {"Ticket ID": "TKT-6541", "Category": "Account Management", "Status": "Resolved", "Resolution": "Plan upgrade applied", "Resolved Date": "2026-08-28"}
    ])
    st.dataframe(mock_history, use_container_width=True)

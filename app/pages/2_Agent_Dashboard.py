import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config_loader import load_departments_config, load_categories_config

st.set_page_config(page_title="Agent Command Center — SupportNova", page_icon="🎧", layout="wide")

# Role Access Check
if st.session_state.get("role") not in ["Agent", "Admin"]:
    st.error("⛔ Access Denied. Restricted to Support Agents.")
    st.info("Switch active role to 'Agent' in the sidebar or log in.")
    st.stop()

st.title("🎧 Support Agent Command Center")
st.caption("AI-assisted complaint processing & dual-pipeline validation workbench.")

# KPI Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Pending Queue", "14 Tickets", delta="-4 Today")
col2.metric("SLA At-Risk", "2 Tickets", delta="Critical", delta_color="inverse")
col3.metric("GenAI Accuracy", "96.4%", delta="+1.2%")
col4.metric("Avg Resolution Time", "42 mins", delta="-8 mins")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["⚡ Assigned Work Queue", "🤖 AI Resolution Workbench", "📊 Department Queue SLA"])

with tab1:
    st.subheader("High-Priority Complaints Assigned to You")
    mock_agent_queue = pd.DataFrame([
        {"Ticket ID": "TKT-8842", "Customer": "Sarah Jenkins", "Category": "Billing", "Subcategory": "Incorrect Charge", "Priority Weight": 9, "SLA Remaining": "2h 15m", "AI Confidence": "98%"},
        {"Ticket ID": "TKT-8901", "Customer": "Robert Paulson", "Category": "Network Ops", "Subcategory": "No Signal", "Priority Weight": 10, "SLA Remaining": "0h 45m", "AI Confidence": "91%"},
        {"Ticket ID": "TKT-8945", "Customer": "Alicia Keys", "Category": "Security", "Subcategory": "SIM Swap Suspected", "Priority Weight": 10, "SLA Remaining": "0h 18m", "AI Confidence": "99%"}
    ])
    st.dataframe(mock_agent_queue, use_container_width=True)

with tab2:
    st.subheader("Dual-Pipeline Ticket Workbench (TKT-8842)")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("#### 🧠 GenAI Classification & Draft")
        st.json({
            "detected_intent": "Dispute over promotional rate expiration",
            "sentiment_score": -0.82,
            "suggested_category": "BILLING",
            "suggested_subcategory": "BILLING_PROMO_NOT_APPLIED",
            "proposed_credit_usd": 30.00,
            "draft_response": "Dear Customer, we apologize for the promotion code delay. A $30 credit has been applied."
        })
    
    with col_b:
        st.markdown("#### 🐍 Python Ground-Truth Verification")
        st.json({
            "rule_check_passed": True,
            "contract_valid": True,
            "max_authorized_credit_usd": 50.00,
            "pii_scrubbed": True,
            "dual_pipeline_alignment": "MATCH",
            "hallucination_flag": False
        })
    
    with st.form("agent_action_form"):
        st.markdown("#### 📝 Agent Final Approval")
        agent_response = st.text_area("Resolution Message to Customer:", "Dear Customer, we apologize for the promotion code delay. A $30 credit has been applied to your next invoice.")
        credit_amount = st.number_input("Approved Credit ($USD):", min_value=0.0, max_value=100.0, value=30.0)
        action = st.selectbox("Action:", ["Approve & Dispatch Resolution", "Escalate to Reviewer Queue", "Request Field Technician"])
        
        submitted = st.form_submit_button("🚀 Submit Decision")
        if submitted:
            st.success(f"Action '{action}' executed successfully for TKT-8842!")

with tab3:
    st.subheader("Department Queue SLA Breakdown")
    fig = px.bar(
        x=["Billing", "Network Ops", "Security", "Field Ops", "IPTV"],
        y=[14, 22, 3, 9, 7],
        labels={'x': 'Department', 'y': 'Active Complaints'},
        title="Active Complaints by Department",
        color_discrete_sequence=['#3B82F6']
    )
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#F8FAFC')
    st.plotly_chart(fig, use_container_width=True)

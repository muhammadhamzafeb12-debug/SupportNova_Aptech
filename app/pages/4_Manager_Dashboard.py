import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

st.set_page_config(page_title="Manager Analytics — SupportNova", page_icon="📈", layout="wide")

# Role check
if st.session_state.get("role") not in ["Manager", "Admin"]:
    st.error("⛔ Access Denied. Restricted to Department Managers.")
    st.info("Switch role to 'Manager' in the sidebar.")
    st.stop()

st.title("📈 Manager Operational Command Center")
st.caption("High-level throughput, SLA compliance metrics, and escalation management.")

# Top KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Inflow (24h)", "342 Tickets", delta="+12%")
col2.metric("SLA Compliance Rate", "98.1%", delta="+0.4%")
col3.metric("Auto-Resolution Rate", "64.5%", delta="+3.1%")
col4.metric("Total Credits Issued", "$4,280.00", delta="Within Budget")

st.markdown("---")

tab1, tab2 = st.tabs(["📊 SLA & Department Analytics", "🚨 Escalation Risk Radar"])

with tab1:
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Complaints by Category (Last 7 Days)")
        df_cat = pd.DataFrame({
            "Category": ["Billing", "Network", "Device", "Account", "Security", "IPTV"],
            "Count": [120, 95, 40, 35, 15, 37]
        })
        fig1 = px.pie(df_cat, values='Count', names='Category', color_discrete_sequence=px.colors.sequential.Blues_r)
        fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#F8FAFC')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_right:
        st.subheader("Resolution Time Trend (Hours)")
        df_trend = pd.DataFrame({
            "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "Avg Hours": [4.2, 3.8, 3.5, 3.1, 2.9, 2.4, 2.1]
        })
        fig2 = px.line(df_trend, x='Day', y='Avg Hours', markers=True, color_discrete_sequence=['#3B82F6'])
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#F8FAFC')
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("🚨 High-Risk Escalation Candidates")
    df_esc = pd.DataFrame([
        {"Ticket ID": "TKT-8945", "Customer": "Alicia Keys", "Department": "Security", "Issue": "SIM Swap Suspected", "SLA Status": "18m Left", "Executive Flag": "YES"},
        {"Ticket ID": "TKT-8890", "Customer": "Global Logistics Inc", "Department": "Network Ops", "Issue": "Enterprise Fiber Outage", "SLA Status": "35m Left", "Executive Flag": "YES"}
    ])
    st.dataframe(df_esc, use_container_width=True)

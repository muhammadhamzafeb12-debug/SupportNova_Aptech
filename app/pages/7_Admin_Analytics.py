import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

st.set_page_config(page_title="Platform Analytics — SupportNova", page_icon="📊", layout="wide")

# Role check
if st.session_state.get("role") != "Admin":
    st.error("⛔ Access Denied. Restricted to System Administrators.")
    st.info("Switch role to 'Admin' in the sidebar.")
    st.stop()

st.title("📊 Platform System Analytics")
st.caption("Dual-pipeline performance, GenAI latency metrics, and API cost usage.")

# System Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("GenAI API Calls (24h)", "1,420 Calls", delta="+8%")
col2.metric("Avg Latency", "1.24s", delta="-0.15s")
col3.metric("Estimated Cost", "$14.20", delta="Budget OK")
col4.metric("Dual-Pipeline Match Rate", "97.6%", delta="+0.8%")

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("API Latency Distribution (ms)")
    df_lat = pd.DataFrame({
        "Pipeline Step": ["Ingestion & PII Scrubbing", "GenAI Classification", "Python Ground-Truth", "FAISS RAG Lookup", "Dual Alignment Check"],
        "Latency (ms)": [45, 850, 12, 110, 25]
    })
    fig1 = px.bar(df_lat, x="Pipeline Step", y="Latency (ms)", color="Latency (ms)", color_continuous_scale="Blues")
    fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#F8FAFC')
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    st.subheader("GenAI vs Ground-Truth Agreement")
    df_agree = pd.DataFrame({
        "Status": ["Exact Match", "Minor Subcategory Difference", "Financial Limit Override Required"],
        "Count": [1240, 45, 15]
    })
    fig2 = px.pie(df_agree, values="Count", names="Status", color_discrete_sequence=px.colors.sequential.Teal)
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#F8FAFC')
    st.plotly_chart(fig2, use_container_width=True)

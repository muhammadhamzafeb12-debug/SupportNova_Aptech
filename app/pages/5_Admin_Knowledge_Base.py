import streamlit as st
import pandas as pd
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

st.set_page_config(page_title="Knowledge Base Admin — SupportNova", page_icon="📚", layout="wide")

# Role check
if st.session_state.get("role") != "Admin":
    st.error("⛔ Access Denied. Restricted to System Administrators.")
    st.info("Switch role to 'Admin' in the sidebar.")
    st.stop()

st.title("📚 RAG Knowledge Base Management")
st.caption("Upload SOP documents, index policy contracts, and maintain vector search index.")

col1, col2, col3 = st.columns(3)
col1.metric("Indexed Documents", "42 Docs", delta="+3 This Week")
col2.metric("Vector Chunks", "1,280 Chunks", delta="FAISS Active")
col3.metric("Search Latency", "12 ms", delta="-2 ms")

st.markdown("---")

tab1, tab2 = st.tabs(["📄 Document Indexer", "🔍 Knowledge Base Search Test"])

with tab1:
    st.subheader("Upload Policy / SLA Document for Indexing")
    uploaded_file = st.file_uploader("Upload PDF or DOCX policy file:", type=["pdf", "docx", "txt"])
    doc_category = st.selectbox("Document Scope:", ["Billing Policy", "Network SLA", "Device Warranty", "Regulatory Standards"])
    
    if st.button("⚡ Process & Index Document"):
        if uploaded_file:
            st.success(f"File '{uploaded_file.name}' processed! Created 34 chunks in FAISS index under '{doc_category}'.")
        else:
            st.warning("Please select a file first.")

    st.markdown("### Existing Knowledge Base Repository")
    kb_data = pd.DataFrame([
        {"Doc ID": "KB-101", "Title": "NexaLink Refund & Credit Guidelines 2026.pdf", "Scope": "Billing Policy", "Chunks": 45, "Last Updated": "2026-09-20"},
        {"Doc ID": "KB-102", "Title": "5G Coverage SLA & Outage Credits.docx", "Scope": "Network SLA", "Chunks": 32, "Last Updated": "2026-09-18"},
        {"Doc ID": "KB-103", "Title": "FCC Regulatory Dispute Handling Protocol.pdf", "Scope": "Regulatory Standards", "Chunks": 60, "Last Updated": "2026-09-15"}
    ])
    st.dataframe(kb_data, use_container_width=True)

with tab2:
    st.subheader("Vector Similarity Query Sandbox")
    query = st.text_input("Enter test query:", "What is the maximum refund limit for promotional pricing errors?")
    if st.button("Search Knowledge Base"):
        st.markdown("#### Top Matching Chunks (Cosine Similarity Score)")
        st.info("📄 **Match 1 (Score: 0.92):** KB-101 (Chunk 12) — 'Section 4.2: Billing representatives are authorized to issue up to $50 credit for verified promotional discrepancy without manager approval.'")
        st.info("📄 **Match 2 (Score: 0.84):** KB-101 (Chunk 14) — 'Section 4.4: Credits exceeding $50 require dual-pipeline escalation to Reviewer Queue.'")

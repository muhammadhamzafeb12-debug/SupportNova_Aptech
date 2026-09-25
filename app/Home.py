import streamlit as st
import sys
from pathlib import Path

# Add project root to path for clean backend imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config_loader import load_organization_config, load_categories_config, load_departments_config
from backend.security.auth import get_available_roles

st.set_page_config(
    page_title="SupportNova — AI Customer Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphism CSS styling
st.markdown("""
<style>
    .stApp {
        background-color: #0B0F19;
        color: #F3F4F6;
    }
    .hero-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        color: white;
        margin-bottom: 1rem;
    }
    .stat-box {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State for Authentication & Role
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = "Guest"
if "role" not in st.session_state:
    st.session_state["role"] = "Guest"
if "full_name" not in st.session_state:
    st.session_state["full_name"] = "Guest User"

# Load organization config via backend module
org_config = load_organization_config()
org = org_config.get("organization", {})
categories_config = load_categories_config()
departments_config = load_departments_config()

# Top Bar / Sidebar Auth Status
st.sidebar.markdown(f"### 🛡️ User Context")
st.sidebar.info(f"**Logged User:** {st.session_state['full_name']}\n\n**Role:** `{st.session_state['role']}`")

# Quick Role Switcher for Scaffolding / Dev Mode
st.sidebar.markdown("---")
st.sidebar.markdown("##### ⚙️ Dev Role Switcher")
selected_role = st.sidebar.selectbox("Simulate Role:", get_available_roles(), index=get_available_roles().index(st.session_state["role"]) if st.session_state["role"] in get_available_roles() else 0)
if st.sidebar.button("Switch Active Role"):
    st.session_state["role"] = selected_role
    st.session_state["authenticated"] = True
    st.session_state["full_name"] = f"Dev {selected_role}"
    st.rerun()

if st.session_state["authenticated"]:
    if st.sidebar.button("Log Out"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = "Guest"
        st.session_state["role"] = "Guest"
        st.session_state["full_name"] = "Guest User"
        st.rerun()

# Main Landing Page Content
st.markdown('<div class="badge">SupportNova Enterprise v1.0</div>', unsafe_allow_html=True)
st.title(f"⚡ SupportNova — {org.get('name', 'NexaLink Communications')}")
st.caption(f"_{org.get('tagline', 'Connecting Every Horizon')}_ | AI-Powered Customer Complaint Resolution Intelligence Platform")

st.markdown("""
<div class="hero-card">
    <h2>Welcome to SupportNova Command Center</h2>
    <p style="color: #9CA3AF; font-size: 1.1rem; line-height: 1.6;">
        SupportNova is a dual-pipeline customer complaint intelligence platform powered by Generative AI and 
        deterministic Python ground-truth rules. Engineered specifically for enterprise operations at 
        <b>NexaLink Communications</b>.
    </p>
</div>
""", unsafe_allow_html=True)

# Overview Metrics from backend configs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Subscribers", "4.2M+", delta="29 States")
with col2:
    st.metric("Products Catalogs", len(org_config.get("product_catalog", [])), delta="Active Catalog")
with col3:
    st.metric("Complaint Taxonomy", f"{len(categories_config.get('categories', []))} Cats", delta="33 Subcategories")
with col4:
    st.metric("Support Departments", len(departments_config.get("departments", [])), delta="SLA Monitored")

st.markdown("---")

st.subheader("📌 Quick Navigation & Role Access")

if not st.session_state["authenticated"]:
    st.warning("🔒 You are currently in Guest mode. Please click below to log in or use the sidebar role switcher.")
    st.page_link("pages/9_Login.py", label="🔑 Go to Login Page", icon="🔐")

st.markdown("""
- **Customer View:** Submit complaints & track ticket resolution.
- **Agent Dashboard:** Process assigned tickets, review GenAI drafts & run ground-truth validation.
- **Reviewer Queue:** Audit dual-pipeline hallucination flags & override AI decisions.
- **Manager Dashboard:** SLA breach tracking & department performance analytics.
- **Admin Suite:** Manage Knowledge Base RAG index, rule matrix, and platform analytics.
""")

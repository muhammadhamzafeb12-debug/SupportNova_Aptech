import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config_loader import load_organization_config, load_categories_config

st.set_page_config(page_title="Submit Complaint — SupportNova", page_icon="📝", layout="wide")

st.title("📝 Customer Complaint Submission")
st.caption("Submit a service issue, billing dispute, or technical complaint to NexaLink Communications.")

org_config = load_organization_config()
cats_config = load_categories_config()
products = org_config.get("product_catalog", [])

cat_names = [c.get("name") for c in cats_config.get("categories", [])]
prod_names = [f"{p.get('name')} ({p.get('type')})" for p in products]

with st.form("complaint_submission_form"):
    st.markdown("### 👤 Subscriber & Service Information")
    col1, col2 = st.columns(2)
    with col1:
        customer_name = st.text_input("Full Name:", value="Sarah Jenkins")
        account_number = st.text_input("NexaLink Account / Line Number:", value="ACC-992041")
    with col2:
        contact_email = st.text_input("Contact Email:", value="sarah.j@example.com")
        affected_product = st.selectbox("Affected Product/Service:", prod_names if prod_names else ["NexaFiber Home 300"])

    st.markdown("---")
    st.markdown("### 💬 Complaint Details")
    
    suggested_cat = st.selectbox("Category (Optional self-select):", cat_names if cat_names else ["Billing & Payments"])
    complaint_title = st.text_input("Subject / Short Summary:", "Billed $30 higher than quoted promotional plan")
    complaint_body = st.text_area(
        "Detailed Complaint Description:",
        "I signed up for NexaFiber Home 300 at $39.99/mo under promotion PROMO2026. However, my latest invoice shows $69.99 plus an extra $10 fee. I request an immediate credit of $30.",
        height=150
    )
    
    attachment = st.file_uploader("Attach Supporting Document (PDF / DOCX / Image):", type=["pdf", "docx", "png", "jpg"])
    
    submitted = st.form_submit_button("🚀 Submit Complaint to SupportNova")

if submitted:
    st.success("✅ Complaint Submitted Successfully!")
    st.info("🎟️ **Assigned Ticket ID:** `TKT-8956` | **Initial SLA Resolution Window:** 24 Hours")
    st.json({
        "ticket_id": "TKT-8956",
        "account_number": account_number,
        "status": "QUEUED_FOR_DUAL_PIPELINE",
        "genai_pipeline_status": "PENDING",
        "ground_truth_status": "PENDING"
    })

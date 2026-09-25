import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.security.auth import authenticate_user

st.set_page_config(page_title="Login — SupportNova", page_icon="🔑", layout="centered")

st.title("🔑 SupportNova Portal Login")
st.caption("Access role-based command center for NexaLink Communications.")

st.markdown("""
<style>
    .login-box {
        background: rgba(30, 41, 59, 0.7);
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

if st.session_state.get("authenticated"):
    st.success(f"Logged in as **{st.session_state['full_name']}** (`{st.session_state['role']}`).")
    if st.button("Log Out"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = "Guest"
        st.session_state["role"] = "Guest"
        st.session_state["full_name"] = "Guest User"
        st.rerun()
else:
    with st.form("login_form"):
        st.subheader("Sign In")
        username = st.text_input("Username / Email:", value="agent@nexalink.com")
        password = st.text_input("Password:", type="password", value="password123")
        
        submitted = st.form_submit_button("Sign In")
        
        if submitted:
            user = authenticate_user(username, password)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["username"] = user["username"]
                st.session_state["role"] = user["role"]
                st.session_state["full_name"] = user["full_name"]
                st.success(f"Welcome back, {user['full_name']}!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

    st.markdown("---")
    st.markdown("##### 💡 Demo Credentials (Password: `password123`)")
    st.code("""
Customer:  customer@nexalink.com
Agent:     agent@nexalink.com
Reviewer:  reviewer@nexalink.com
Manager:   manager@nexalink.com
Admin:     admin@nexalink.com
    """)

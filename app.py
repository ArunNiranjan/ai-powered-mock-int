"""
app.py - MockIQ Streamlit Edition

Entry point - shows the landing page when the user is not logged in,
or redirects to the dashboard once authenticated.
"""

import os
import sys

# Make sure 'core' package is importable regardless of cwd
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
from dotenv import load_dotenv

from core.database import init_db
from core.auth import register_user, login_user

load_dotenv()
init_db()

# -- Page config
st.set_page_config(
    page_title="MockIQ | AI Mock Interview",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Session-state defaults
if "user" not in st.session_state:
    st.session_state.user = None


# -- Sidebar nav hint
if st.session_state.user:
    st.sidebar.success(f"Logged in as **{st.session_state.user['name']}**")
    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.rerun()
else:
    st.sidebar.info("Log in or register to start an interview.")


# -- Landing hero
st.markdown(
    """
    <style>
        .hero-title { font-size:3.2rem; font-weight:800; color:#4F8EF9; margin-bottom:0.2rem; }
        .hero-sub { font-size:1.25rem; color:#555; margin-bottom:1.5rem; }
        .feature-card { background:#f7f9fc; border-radius:12px; padding:1rem 1.2rem; margin-bottom:0.6rem; color:#111111; }
        .feature-card strong{ color:#111111; }
        .feature-card small{ color:#333333; }
        .feature-icon { font-size:1.6rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero-title">MockIQ</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">AI-Powered Mock Interview Platform - GPT-4o · Whisper STT · Webcam Emotion Analysis</div>',
    unsafe_allow_html=True,
)

col_feat, col_auth = st.columns([3, 2], gap="large")

with col_feat:
    st.subheader("Key Features")
    features = [
        ("🎯", "GPT-4o Question Generation", "Role-specific, personalised questions via RAG over your uploaded resume."),
        ("🎙️", "Whisper Speech-to-Text", "Record your answer with one click - OpenAI Whisper transcribes it instantly."),
        ("📷", "Webcam Emotion Analysis", "MediaPipe + DeepFace track engagement and emotion in real time."),
        ("💡", "Per-Answer AI Feedback", "Score (0-10), strengths, improvements, and an ideal-answer outline."),
        ("📊", "Session Dashboard", "Full history with expandable per-question breakdowns."),
        ("🔐", "Secure Local Auth", "Register / log in - credentials stored locally in SQLite."),
    ]
    for icon, title, desc in features:
        st.markdown(
            f'<div class="feature-card"><span class="feature-icon">{icon}</span> '
            f'<strong>{title}</strong><br><small>{desc}</small></div>',
            unsafe_allow_html=True,
        )

with col_auth:
    if st.session_state.user:
        st.success(f"Welcome back, **{st.session_state.user['name']}**! 👋")
        st.markdown("Use the sidebar to navigate to your dashboard or start a new interview.")
        if st.button("Go to Dashboard ➔", type="primary", use_container_width=True):
            st.switch_page("pages/4_Dashboard.py")
        if st.button("Start New Interview ➔", use_container_width=True):
            st.switch_page("pages/1_Setup_Interview.py")
    else:
        tab_login, tab_register = st.tabs(["Log In", "Register"])
        
        # -- Login
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
                
            if submitted:
                if not email or not password:
                    st.error("Please enter email and password.")
                else:
                    result = login_user(email, password)
                    if result["success"]:
                        st.session_state.user = result["user"]
                        st.success(f"Welcome back, {result['user']['name']}!")
                        st.rerun()
                    else:
                        st.error(result["message"])
                        
        # -- Register
        with tab_register:
            with st.form("register_form"):
                reg_name = st.text_input("Full Name", placeholder="Jane Doe")
                reg_email = st.text_input("Email", placeholder="jane@example.com")
                reg_password = st.text_input("Password (min 6 chars)", type="password")
                reg_confirm = st.text_input("Confirm Password", type="password")
                reg_submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)
                
            if reg_submit:
                if reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                # elif len(reg_password) < 6:
                #     st.error("Password must be at least 6 characters.")
                else:
                    result = register_user(reg_name, reg_email, reg_password)
                    if result["success"]:
                        st.session_state.user = result["user"]
                        st.success("Account created! Redirecting...")
                        st.rerun()
                    else:
                        st.error(result["message"])
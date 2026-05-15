"""
pages/3_Interview_Complete.py
Results page - per-question breakdown + GPT-4o coaching summary.
"""

import os
import sys

# Add parent directory to sys.path to allow core imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from dotenv import load_dotenv

from core.interview import get_interview_summary

load_dotenv()

st.set_page_config(page_title="Results - MockIQ", page_icon="🏆", layout="wide")

# -- Auth guard
if not st.session_state.get("user"):
    st.warning("Please log in first.")
    st.switch_page("app.py")
    st.stop()

interview = st.session_state.get("interview")
if not interview or not interview.get("feedback"):
    st.warning("No interview results found.")
    st.switch_page("pages/1_Setup_Interview.py")
    st.stop()

feedback = interview["feedback"]
answers = interview["answers"]
questions = interview["questions"]

# -- Score computation
scores = [f.get("score", 0) for f in feedback if isinstance(f, dict)]
overall = sum(scores) / len(scores) if scores else 0.0

# -- Header
st.title("🏆 Interview Complete!")
st.markdown(f"""
**Role:** {interview['job_role']} | 
**Company:** {interview['company']} | 
**Level:** {interview['exp_level']}
""")

# Overall score banner
score_color = "#28a745" if overall >= 7 else "#ffc107" if overall >= 4 else "#dc3545"
st.markdown(
    f"""
    <div style="background:{score_color}22; border-left:6px solid {score_color}; 
                padding:1.2rem 1.5rem; border-radius:8px; margin-bottom:1.5rem;">
        <h2 style="color:{score_color}; margin:0;">Overall Score: {overall:.1f} / 10</h2>
        <p style="margin:0.3rem 0 0; color:#444;">{len(scores)} questions answered</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -- GPT-4o coaching summary
st.subheader("🤖 AI Coaching Summary")
with st.spinner("Generating coaching summary..."):
    summary = get_interview_summary(feedback, interview["job_role"])

if summary:
    st.info(summary.get("overall_summary", ""))

    rec_col, str_col = st.columns(2)
    with rec_col:
        st.markdown("**Recommendations for Improvement**")
        for i, rec in enumerate(summary.get("recommendations", []), 1):
            st.markdown(f"{i}. {rec}")
    with str_col:
        st.markdown("**Key Strength**")
        st.success(summary.get("top_strength", ""))

st.divider()

# -- Per-question breakdown
st.subheader("🔍 Question-by-Question Breakdown")

for i, (q, ans, fb) in enumerate(zip(questions, answers, feedback)):
    score = fb.get("score", 0) if isinstance(fb, dict) else 0
    color = "#28a745" if score >= 7 else "#ffc107" if score >= 4 else "#dc3545"
    label = f"Q{q['id']} - Score: {score}/10"
    
    with st.expander(label):
        st.markdown(f"**Question:** {q['question']}")
        if ans:
            st.markdown(f"**Your Answer:** {ans}")
        else:
            st.markdown("*Question was skipped.*")
            
        if isinstance(fb, dict) and "strength" in fb:
            c1, c2 = st.columns(2)
            with c1:
                st.success(f"**Strength:** {fb.get('strength', '')}")
            with c2:
                st.warning(f"**Improvement:** {fb.get('improvement', '')}")
            
            with st.container():
                st.markdown(f"**💡 Suggested Answer:** {fb.get('suggested_answer', '')}")
            
            kw_col1, kw_col2 = st.columns(2)
            with kw_col1:
                if fb.get("keywords_mentioned"):
                    st.markdown("**Keywords:** " + ", ".join(fb["keywords_mentioned"]))
            with kw_col2:
                if fb.get("missing_keywords"):
                    st.markdown("**❌ Missing:** " + ", ".join(fb["missing_keywords"]))

st.divider()

# -- Navigation
nav1, nav2 = st.columns(2)
with nav1:
    if st.button("🔄 Start Another Interview", use_container_width=True):
        # Clear interview state
        for key in ["interview", "q_index", "transcription", "engagement_score", "face_analyzer"]:
            st.session_state.pop(key, None)
        # Clear per-question feedback keys
        for key in list(st.session_state.keys()):
            if key.startswith("feedback_") or key.startswith("audio_") or key.startswith("answer_text_"):
                st.session_state.pop(key, None)
        st.switch_page("pages/1_Setup_Interview.py")

with nav2:
    if st.button("📊 View Dashboard", use_container_width=True, type="primary"):
        st.switch_page("pages/4_Dashboard.py")
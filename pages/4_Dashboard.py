"""
pages/4_Dashboard.py
Session history dashboard - lists all past interviews with expandable details.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))) # Add parent directory to path

import streamlit as st
from dotenv import load_dotenv

from core.interview import get_interview_history

load_dotenv()

st.set_page_config(page_title="Dashboard - MockIQ", page_icon="📊", layout="wide")

# -- Auth guard
if not st.session_state.get("user"):
    st.warning("Please log in first.")
    st.switch_page("app.py")
    st.stop()

user = st.session_state.user

# -- Header
st.title("📊 Your Interview Dashboard")
st.markdown(f"Showing all sessions for **{user['name']}**.")

if st.button("➕ New Interview", type="primary"):
    # Clear any previous interview state
    for key in ["interview", "q_index", "transcription", "engagement_score"]:
        st.session_state.pop(key, None)
    for key in list(st.session_state.keys()):
        if key.startswith("feedback_") or key.startswith("audio_") or key.startswith("answer_text_"):
            del st.session_state[key]   
    st.switch_page("pages/1_Setup_Interview.py")

st.divider()

# -- Load history
with st.spinner("Loading session history..."):
    history = get_interview_history(user["id"])

if not history:
    st.info("No interview sessions yet. Start your first interview to see results here!")
    st.stop()

# -- Summary metrics
all_scores = [s["overall_score"] for s in history if s["overall_score"] is not None]
avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
best_score = max(all_scores) if all_scores else 0.0

m1, m2, m3 = st.columns(3)
m1.metric("Total Sessions", len(history))
m2.metric("Average Score", f"{avg_score:.1f} / 10")
m3.metric("Best Score", f"{best_score:.1f} / 10")

st.divider()

# -- Session list
st.subheader("Session History")

for s in history:
    score = s.get("overall_score", 0.0) or 0.0
    score_color = "#28a745" if score >= 7 else "#ffc107" if score >= 4 else "#dc3545"
    created = s.get("created", "")[:10] # just date
    
    header = (
        f"**{s['job_role']}** at **{s['company']}** | "
        f"({s['exp_level']}) | ({s['question_type']}) | "
        f"Score: **{score:.1f}/10** | ({created})"
    )
    
    with st.expander(header):
        feedback = s.get("feedback", [])
        questions = s.get("questions", [])
        answers = s.get("answers", [])
        
        if not questions:
            st.write("No question data available.")
            continue
            
        for i, q in enumerate(questions):
            fb = feedback[i] if i < len(feedback) else {}
            ans = answers[i] if i < len(answers) else ""
            q_score = fb.get("score", 0) if isinstance(fb, dict) else 0
            q_label = f"Q{q.get('id', i+1)} - {q.get('question', '')[:80]}... (Score: {q_score}/10)"
            
            with st.container():
                st.markdown(f"**Q{q.get('id', i+1)}.** {q.get('question', '')}")
                if ans:
                    st.markdown(f"*Your answer:* {ans[:300]}{'...' if len(ans) > 300 else ''}")
                
                if isinstance(fb, dict) and "strength" in fb:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.success(f"**Strength:** {fb.get('strength', '')}")
                    with c2:
                        st.warning(f"**Improvement:** {fb.get('improvement', '')}")
                        st.markdown(f"**Score:** {q_score}/10")
                st.markdown("---")
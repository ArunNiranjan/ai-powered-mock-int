"""
pages/1_Setup_Interview.py
Interview setup form - job details + optional resume upload.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from dotenv import load_dotenv

from core.resume import upload_and_index_resume
from core.interview import generate_questions

load_dotenv()

# -- Auth guard
if not st.session_state.get("user"):
    st.warning("Please log in first.")
    st.switch_page("app.py")
    st.stop()

st.set_page_config(page_title="Setup Interview - MockIQ", page_icon="📝", layout="wide")

user = st.session_state.user

st.title("📝 Interview Setup")
st.markdown(f"Hello **{user['name']}** - fill in the details below and click **Generate Questions**.")

# -- Form
with st.form("setup_form"):
    col1, col2 = st.columns(2)

    with col1:
        job_role = st.text_input(
            "Job Role *",
            placeholder="e.g. Senior Software Engineer",
            help="The role you are interviewing for."
        )
        company = st.text_input(
            "Company",
            placeholder="e.g. Acme Corp",
            help="Optional - used to personalise questions."
        )
        exp_level = st.selectbox(
            "Experience Level *",
            ["Entry-level", "Mid-level", "Senior", "Lead / Principal", "Manager"]
        )

    with col2:
        q_type = st.selectbox(
            "Question Type *",
            ["Technical", "Behavioral", "System Design", "Mixed"]
        )
        job_desc = st.text_area(
            "Job Description (optional)",
            placeholder="Paste the JD here for more relevant questions...",
            height=120
        )

    resume_file = st.file_uploader(
        "Upload your Resume (PDF, optional)",
        type=["pdf"],
        help="Your resume is chunked and stored locally in ChromaDB for RAG-based question generation."
    )

    submitted = st.form_submit_button("✨ Generate Questions", type="primary", use_container_width=True)

# -- On submit
if submitted:
    if not job_role.strip():
        st.error("Job Role is required.")
        st.stop()

    # Upload resume if provided
    if resume_file is not None:
        with st.spinner("Indexing resume..."):
            result = upload_and_index_resume(resume_file.read(), user["id"])
            if result["success"]:
                st.success(f"Resume indexed - {result['chunks']} chunks stored.")
            else:
                st.warning(f"Resume indexing failed: {result['message']}. Proceeding without resume.")

    # Generate questions
    with st.spinner("Generating questions with GPT-4o..."):
        result = generate_questions(
            user_id=user["id"],
            job_role=job_role.strip(),
            company=company.strip() or "the company",
            exp_level=exp_level,
            q_type=q_type,
            job_desc=job_desc.strip(),
        )

    if result["success"]:
        # Store interview data in session state for the live interview page
        st.session_state.interview = {
            "session_id": result["session_id"],
            "questions": result["questions"],
            "job_role": job_role.strip(),
            "company": company.strip() or "the company",
            "exp_level": exp_level,
            "question_type": q_type,
            "answers": [],
            "feedback": [],
        }
        st.success(f"✅ {len(result['questions'])} questions generated!")

        with st.expander("Preview Questions"):
            for q in result["questions"]:
                st.markdown(f"**Q{q['id']}:** {q['question']}")

        st.info("Click **Live Interview** in the sidebar to begin.")
        if st.button("Start Interview ➔", type="primary"):
            st.switch_page("pages/2_Live_Interview.py")
    else:
        st.error(f"Failed to generate questions: {result['message']}")
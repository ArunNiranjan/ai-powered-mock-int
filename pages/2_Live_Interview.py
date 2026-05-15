"""
pages/2_Live_Interview.py
Live Interview - webcam emotion tracking (streamlit-webrtc),
audio recording (st.audio_input), per-answer GPT-4o feedback.
"""

import os
import sys
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))   # Add parent directory to sys.path

import streamlit as st
from dotenv import load_dotenv

from core.interview import get_feedback, transcribe_audio, save_interview
from core.face_analyzer import FaceAnalyzer

load_dotenv()

st.set_page_config(page_title="Live Interview - MockIQ", page_icon="🎥", layout="wide")

# -- Auth guard
if not st.session_state.get("user"):
    st.warning("Please log in first.")
    st.switch_page("app.py")
    st.stop()

if not st.session_state.get("interview"):
    st.warning("No interview session found. Please complete the setup first.")
    st.switch_page("pages/1_Setup_Interview.py")
    st.stop()

user = st.session_state.user
interview = st.session_state.interview
questions = interview["questions"]
n_q = len(questions)

# Current question index
if "q_index" not in st.session_state:
    st.session_state.q_index = 0

q_index = st.session_state.q_index

# -- Header
st.title("🎥 Live Interview")
st.markdown(
    f"**Role:** {interview['job_role']} &nbsp;|&nbsp; "
    f"**Company:** {interview['company']} &nbsp;|&nbsp; "
    f"**Level:** {interview['exp_level']} &nbsp;|&nbsp; "
    f"**Type:** {interview['question_type']}"
)

progress_val = q_index / n_q
st.progress(progress_val, text=f"Question {q_index + 1} of {n_q}")

# -- Layout
col_main, col_cam = st.columns([3, 2], gap="large")

with col_main:
    # Current question
    current_q = questions[q_index]
    st.subheader(f"Q{current_q['id']}.")
    st.markdown(f"### {current_q['question']}")

    st.divider()

    # -- Audio recording
    st.markdown("**🎙️ Record Your Answer**")
    audio_value = st.audio_input(
        "Press the mic button to record, then release to stop.",
        key=f"audio_{q_index}",
    )

    # Transcription display
    if "transcription" not in st.session_state:
        st.session_state.transcription = ""

    if audio_value is not None:
        with st.spinner("Transcribing with Whisper..."):
            text = transcribe_audio(audio_value.read(), mime_type=audio_value.type)
            st.session_state.transcription = text

    # Editable text area - user can correct the transcription
    answer_text = st.text_area(
        "Your Answer (edit if needed)",
        value=st.session_state.transcription,
        height=150,
        key=f"answer_text_{q_index}",
        placeholder="Speak above, or type your answer here...",
    )

    # -- Engagement score (placeholder for calculation)
    engagement_score = st.session_state.get("engagement_score", 50.0)

    # -- Submit / Skip buttons
    submit_col, skip_col = st.columns([2, 1])
    with submit_col:
        submit_btn = st.button(
            "Submit Answer & Get Feedback",
            type="primary",
            use_container_width=True,
            disabled=not answer_text.strip(),
        )
    with skip_col:
        skip_btn = st.button("Skip Question ➔", use_container_width=True)

    # -- Feedback display
    if f"feedback_{q_index}" in st.session_state:
        fb = st.session_state[f"feedback_{q_index}"]
        if isinstance(fb, dict) and "score" in fb:
            score = fb["score"]
            color = "#28a745" if score >= 7 else "#ffc107" if score >= 4 else "#dc3545"
            st.markdown(
                f"<h3 style='color: {color}'>Score: {score}/10</h3>",
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns(2)
            with c1:
                st.success(f"**Strength:** {fb.get('strength', '')}")
            with c2:
                st.warning(f"**Improvement:** {fb.get('improvement', '')}")

            with st.expander("💡 Suggested Ideal Answer"):
                st.write(fb.get("suggested_answer", ""))

            kw_col1, kw_col2 = st.columns(2)
            with kw_col1:
                if fb.get("keywords_mentioned"):
                    st.markdown("**✅ Keywords Mentioned:**")
                    st.write(", ".join(fb["keywords_mentioned"]))
            with kw_col2:
                if fb.get("missing_keywords"):
                    st.markdown("**❌ Missing Keywords:**")
                    st.write(", ".join(fb["missing_keywords"]))

            st.info(f"***Engagement Note:** {fb.get('engagement_feedback', '')}")

            # Next / Finish button
            if q_index < n_q - 1:
                if st.button("Next Question ➔", type="primary"):
                    st.session_state.q_index += 1
                    st.session_state.transcription = ""
                    st.rerun()
            else:
                if st.button("Finish Interview 🏁", type="primary"):
                    save_interview(
                        user_id=user["id"],
                        session_id=interview["session_id"],
                        answers=interview["answers"],
                        feedback=interview["feedback"],
                    )
                    st.switch_page("pages/3_Interview_Complete.py")

# -- Webcam panel
with col_cam:
    st.markdown("**📷 Webcam - Emotion & Engagement**")

    #Try streamlit-webrtc for realtime processing; fail back to st.camera_input if not available. Results are stored in session state for feedback context.
    try:
        from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
        import av
        import numpy as np

        class _EmotionProcessor(VideoProcessorBase):
            def __init__(self) -> None:
                self.analyzer = FaceAnalyzer()

            def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
                img = frame.to_ndarray(format="bgr24")
                self.analyzer.process_frame(img)
                return frame

            def get_result(self) -> dict:
                return self.analyzer.get_last_result()

        ctx = webrtc_streamer(
            key="emotion-can",
            video_processor_factory=_EmotionProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        if ctx.video_processor:
            result = ctx.video_processor.get_result()
            emotion = result.get("emotion", "neutral")
            engagement = result.get("engagement_score", 0.5)
            positivity = result.get("positivity_score", 0.5)

            # Store engagement score in session state for feedback context
            st.session_state.engagement_score = engagement * 100

            EMOTION_EMOJI = {
                "happy": "😊", "surprise": "😮", "neutral": "😐",
                "angry": "😠", "sad": "😢", "fear": "😨", "disgust": "🤢",
            }
            st.metric("Emotion", f"{EMOTION_EMOJI.get(emotion, '😐')} {emotion.capitalize()}")
            st.metric("Engagement", f"{engagement * 100:.0f}%")
            st.metric("Positivity", f"{positivity * 100:.0f}%")

    except ImportError:
        #Fallback periodic snapshot mode if streamlit-webrtc isn't installed or fails to load (e.g. on unsupported platforms) via st.camera_input
        st.info("For real-time emotion analysis install `streamlit-webrtc`. Using snapshot mode.")
        snapshot = st.camera_input("Take a snapshot for emotion analysis")

        if snapshot is not None:
            import cv2
            import numpy as np
            from PIL import Image

            img_pil = Image.open(snapshot)
            img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

            if "face_analyzer" not in st.session_state:
                st.session_state.face_analyzer = FaceAnalyzer()

            result = st.session_state.face_analyzer.process_frame(img_bgr)
            if result and result.get("status") == "ok":
                emotion = result.get("emotion", "neutral")
                engagement = result.get("engagement_score", 0.5)
                st.session_state.engagement_score = engagement * 100
                st.metric("Emotion", emotion.capitalize())
                st.metric("Engagement", f"{engagement * 100:.0f}%")

    st.divider()
    st.markdown(f"**Progress:** {len(interview['answers'])} / {n_q} answered"
    )


# -- Handle submit/ skip (Bottom of script)
if submit_btn and answer_text.strip():
    with st.spinner("Getting GPT-4o feedback..."):
        fb = get_feedback(
            question=current_q["question"],
            answer=answer_text.strip(),
            job_role=interview["job_role"],
            q_type=interview["question_type"],
            engagement_pct=st.session_state.get("engagement_score", 50.0),
        )
    # Persistant in session state for display and context in next questions; also appended to interview data for final storage
    st.session_state[f"feedback_{q_index}"] = fb
    interview["answers"].append(answer_text.strip())
    interview["feedback"].append(fb)
    st.rerun()

if skip_btn:
    interview["answers"].append("")
    interview["feedback"].append({"score": 0, "strength": "Skipped", "improvement": "Skipped", "suggested_answer": "", "keywords_mentioned": [], "missing_keywords": [], "engagement_feedback": "Skipped"})
    
    if q_index < n_q - 1:
        st.session_state.q_index += 1
        st.session_state.transcription = ""
        st.rerun()
    else:
        save_interview(
            user_id=user["id"],
            session_id=interview["session_id"],
            answers=interview["answers"],
            feedback=interview["feedback"],
        )
        st.switch_page("pages/3_Interview_Complete.py")
"""
core/interview.py
Question generation, per-answer feedback, session save/load, overall summary,
and audio transcription (OpenAI Whisper) 🎙️ all using GPT-4o.
"""

import json
import datetime

import streamlit as st

from .database import InterviewSession, get_db
from .resume import get_openai_client, get_resume_context


# -- Question generation --

def generate_questions(
    user_id: int,
    job_role: str,
    company: str,
    exp_level: str,
    q_type: str,
    job_desc: str,
) -> dict:
    """Generate 10 interview questions via GPT-4o + optional RAG over resume."""
    client = get_openai_client()
    resume_context = get_resume_context(user_id, job_role, q_type)
    resume_section = (
        f"- Candidate Resume Highlights: \n{resume_context}" if resume_context else ""
    )
    
    prompt = f"""You are a senior {q_type} interviewer at {company}.
Generate exactly 10 {q_type} interview questions for a {exp_level} {job_role} candidate.

Context:
- Job Description: {job_desc[:800] if job_desc else "Not provided"}
{resume_section}

Rules:
1. Return ONLY valid JSON - no markdown fences, no extra text.
2. Mix conceptual, scenario-based, and problem-solving questions.
3. Calibrate difficulty to {exp_level} level.
4. For Technical: include architecture, debugging, and best-practice questions.
5. For Behavioral: frame using STAR-method prompts.

JSON schema (exactly 10 items):
{{"questions": [{{"id":1, "question":"..."}}, {{"id":2, "question":"..."}}, ..., {{"id":10, "question":"..."}}]}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000,
        )
        result = json.loads(response.choices[0].message.content)
        questions = result.get("questions", [])
        
        with get_db() as db:
            session = InterviewSession(
                user_id=user_id,
                job_role=job_role,
                company=company,
                exp_level=exp_level,
                question_type=q_type,
                questions=json.dumps(questions),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id
            
        return {"success": True, "questions": questions, "session_id": session_id}
    except Exception as exc:
        return {"success": False, "message": str(exc)}


# -- Per-answer feedback --

def get_feedback(
    question: str,
    answer: str,
    job_role: str,
    q_type: str,
    engagement_pct: float,
) -> dict:
    """Evaluate a single answer with GPT-4o and return structured feedback."""
    if not answer or len(answer.strip()) < 5:
        return {
            "score": 0,
            "strength": "No answer was provided.",
            "improvement": "Please record your answer before submitting.",
            "suggested_answer": "",
            "keywords_mentioned": [],
            "missing_keywords": [],
            "engagement_feedback": "No data",
        }
        
    client = get_openai_client()
    prompt = f"""You are an expert {q_type} interviewer. Evaluate this candidate answer fairly and constructively.

Role: {job_role}
Question: {question}
Candidate's Answer: {answer}
Confidence/Engagement Score: {engagement_pct:.0f}/100

Return ONLY valid JSON:
{{
    "score": <integer 0-10>,
    "strength": "<one specific strength in 1-2 sentences>",
    "improvement": "<one actionable improvement in 1-2 sentences>",
    "suggested_answer": "<brief ideal answer outline in 2-3 sentences>",
    "keywords_mentioned": ["<keyword found in answer>"],
    "missing_keywords": ["<important keyword absent from answer>"],
    "engagement_feedback": "<brief note on confidence level based on engagement score>"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=700,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as exc:
        return {"success": False, "message": str(exc)}


# -- Save session --

def save_interview(user_id: int, session_id: int, answers: list, feedback: list) -> dict:
    """Persist answers + feedback and compute overall score."""
    with get_db() as db:
        session = (
            db.query(InterviewSession)
            .filter_by(id=session_id, user_id=user_id)
            .first()
        )
        if not session:
            return {"success": False, "message": "Session not found."}
            
        scores = [f.get("score", 0) for f in feedback if isinstance(f, dict)]
        overall = sum(scores) / len(scores) if scores else 0.0
        
        session.answers = json.dumps(answers)
        session.feedback = json.dumps(feedback)
        session.overall_score = round(overall, 2)
        db.commit()
        
    return {"success": True, "overall_score": overall}


# -- Interview history --

def get_interview_history(user_id: int) -> list[dict]:
    """Return the 20 most recent interview sessions for a user."""
    with get_db() as db:
        sessions = (
            db.query(InterviewSession)
            .filter_by(user_id=user_id)
            .order_by(InterviewSession.created.desc())
            .limit(20)
            .all()
        )
        return [
            {
                "id": s.id,
                "job_role": s.job_role,
                "company": s.company,
                "exp_level": s.exp_level,
                "question_type": s.question_type,
                "overall_score": s.overall_score,
                "questions": json.loads(s.questions) if s.questions else [],
                "answers": json.loads(s.answers) if s.answers else [],
                "feedback": json.loads(s.feedback) if s.feedback else [],
                "created": s.created.isoformat() if s.created else "",
            }
            for s in sessions
        ]


# -- Overall summary --

def get_interview_summary(feedback: list[dict], job_role: str) -> dict:
    """Generate a GPT-4o coaching summary from per-question feedback."""
    if not feedback:
        return {"overall_summary": "No feedback available.", "recommendations": [], "top_strength": ""}
        
    client = get_openai_client()
    feedback_text = "\n".join([
        f"Q{i+1}: Score {f.get('score', 0)}/10 - {f.get('strength', '')} | {f.get('improvement', '')}"
        for i, f in enumerate(feedback)
        if isinstance(f, dict)
    ])
    
    prompt = f"""You are an interview coach. Based on the following per-question feedback for a {job_role} candidate, write:
1. A 1-2 sentence overall performance summary
2. Three concrete recommendations for improvement
3. One key strength to build upon

Feedback summary:
{feedback_text}

Return ONLY valid JSON:
{{
    "overall_summary": "...",
    "recommendations": ["...", "...", "..."],
    "top_strength": "..."
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=500,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as exc:
        return {"overall_summary": str(exc), "recommendations": [], "top_strength": ""}


# -- Audio transcription (OpenAI Whisper) --

def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """Transcribe audio bytes using OpenAI Whisper."""
    import tempfile
    import os
    
    # Determine file extension from mime type
    ext_map = {
        "audio/wav": ".wav",
        "audio/webm": ".webm",
        "audio/ogg": ".ogg",
        "audio/mp4": ".mp4",
        "audio/mpeg": ".mp3",
    }
    ext = ext_map.get(mime_type, ".wav")
    
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
        
    try:
        client = get_openai_client()
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        return transcript.text
    except Exception:
        return ""
    finally:
        os.unlink(tmp_path)
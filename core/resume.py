"""
core/resume.py
PDF ingestion -> chunking -> ChromaDB + OpenAI/Gemini embeddings.
"""

import os
import tempfile

import streamlit as st
from pypdf import PdfReader


@st.cache_resource
def _get_chroma_client():
    import chromadb
    path = os.getenv("CHROMA_PATH", "./chroma_db")
    return chromadb.PersistentClient(path=path)


# @st.cache_resource
# def get_openai_client():
#     from openai import OpenAI
#     return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@st.cache_resource
def get_gemini_client():
    from google import genai
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# def get_embeddings(texts: list[str]) -> list[list[float]]:
#     if not texts:
#         return []
#     client = _get_openai_client()
#     response = client.embeddings.create(model="text-embedding-3-small", input=texts)
#     return [item.embedding for item in response.data]

def get_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    client = get_gemini_client()
    result = client.models.embed_content(
        model="models/text-embedding-004", 
        contents=texts,
    )
    return [e.values for e in result.embeddings]

def upload_and_index_resume(pdf_bytes: bytes, user_id: int) -> dict:
    """
    Parse PDF bytes, chunk the text, embed with OpenAI, store in ChromaDB.
    Returns {"success": bool, "chunks": int | "message": str}.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        reader = PdfReader(tmp_path)
        full_text = "".join([page.extract_text() or "" for page in reader.pages])
        if not full_text.strip():
            return {"success": False, "message": "Could not extract text from the PDF."}

        chunk_size, overlap = 600, 200
        chunks: list[str] = []
        for i in range(0, len(full_text), chunk_size - overlap):
            chunk = full_text[i : i + chunk_size].strip()
            if chunk:
                chunks.append(chunk)

        chroma = _get_chroma_client()
        col_name = f"resume_{user_id}"
        try:
            chroma.delete_collection(col_name)
        except Exception:
            pass

        col = chroma.create_collection(col_name)
        embeddings = get_embeddings(chunks)
        col.add(
            documents=chunks,
            embeddings=embeddings,
            ids=[str(i) for i in range(len(chunks))],
        )
        return {"success": True, "chunks": len(chunks)}

    except Exception as exc:
        return {"success": False, "message": str(exc)}
    finally:
        os.unlink(tmp_path)


def get_resume_context(user_id: int, job_role: str, q_type: str) -> str:
    """Retrieve the most relevant resume snippets for a given job role/type."""
    try:
        chroma = _get_chroma_client()
        col = chroma.get_collection(f"resume_{user_id}")
        q_emb = get_embeddings([f"{job_role} {q_type} skills"])
        results = col.query(query_embeddings=q_emb, n_results=5)
        return "\n".join(results["documents"][0])[:1500]
    except Exception:
        return ""
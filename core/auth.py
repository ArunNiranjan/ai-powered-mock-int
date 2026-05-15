"""
core/auth.py
User registration and login 🔒 no JWT needed; auth state lives in st.session_state.
"""

from werkzeug.security import check_password_hash, generate_password_hash

from .database import User, get_db


def register_user(name: str, email: str, password: str) -> dict:
    """Create a new user. Returns {"success": bool, "user": {...} | "message": str}."""
    email = email.strip().lower()
    name = name.strip()

    if not email or not password:
        return {"success": False, "message": "Email and password are required."}
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters."}
    if not name:
        return {"success": False, "message": "Name is required."}

    with get_db() as db:
        if db.query(User).filter_by(email=email).first():
            return {"success": False, "message": "Email is already registered."}

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "success": True,
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }


def login_user(email: str, password: str) -> dict:
    """Verify credentials. Returns {"success": bool, "user": {...} | "message": str}."""
    email = email.strip().lower()

    with get_db() as db:
        user = db.query(User).filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return {"success": False, "message": "Invalid email or password."}

    return {
        "success": True,
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }
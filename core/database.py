"""
core/database.py
SQLAlchemy models and session management (no Flask dependency).
"""

import os
import datetime
from contextlib import contextmanager

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mockiq.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}, # needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String(100), nullable=False)
    email    = Column(String(120), unique=True, nullable=False, index=True)
    password = Column(String(200), nullable=False)
    created  = Column(DateTime, default=datetime.datetime.utcnow)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_role      = Column(String(200))
    company       = Column(String(200))
    exp_level     = Column(String(50))
    question_type = Column(String(50))
    questions     = Column(Text)          # JSON list
    answers       = Column(Text)          # JSON list
    feedback      = Column(Text)          # JSON list
    overall_score = Column(Float, default=0.0)
    created       = Column(DateTime, default=datetime.datetime.utcnow)


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)


@contextmanager
def get_db():
    """Yield a database session, always close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
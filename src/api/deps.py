"""API 의존성."""

from sqlalchemy.orm import Session
from src.db.session import SessionLocal


def get_db():
    """DB 세션 의존성."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

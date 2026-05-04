"""FastAPI 의존성."""

import os
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from src.db.session import SessionLocal


def get_db() -> Session:
    """DB 세션 의존성."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(x_api_key: str = Header(...)) -> str:
    """API Key 검증."""
    valid_api_key = os.getenv("API_KEY", "test-key")
    if x_api_key != valid_api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

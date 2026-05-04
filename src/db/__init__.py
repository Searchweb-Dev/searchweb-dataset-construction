"""데이터베이스 설정 및 모델 정의."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from .models.base import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/searchweb")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """데이터베이스 세션을 반환합니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 모든 ORM 모델을 import하여 Base에 등록
from . import models  # noqa: E402, F401

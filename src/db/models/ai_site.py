"""AI 웹사이트 ORM 모델."""

from sqlalchemy import Column, BigInteger, String, Boolean, Text, Integer, DateTime
from .base import BaseModel


class AISite(BaseModel):
    """분석된 AI 서비스 웹사이트 정보."""

    __tablename__ = "ai_site"

    site_id = Column(BigInteger, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False, unique=True, index=True)
    canonical_url = Column(String(2048), nullable=True)
    is_ai_tool = Column(Boolean, nullable=False, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    favicon_url = Column(String(2048), nullable=True)
    screenshot_url = Column(String(2048), nullable=True)
    summary_ko = Column(Text, nullable=True)
    score_utility = Column(Integer, nullable=True)
    score_trust = Column(Integer, nullable=True)
    score_originality = Column(Integer, nullable=True)
    last_analyzed_at = Column(DateTime, nullable=True, index=True)

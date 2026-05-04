"""링크 관련 ORM 모델."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Index
from .base import BaseModel


class Link(BaseModel):
    """URL 대상(정규화 URL, 메타 정보, 자동분류 대표 카테고리)."""

    __tablename__ = "link"

    link_id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_url = Column(String, nullable=False, unique=True, index=True)
    original_url = Column(String, nullable=False)
    domain = Column(String(255), nullable=True, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    favicon_url = Column(String, nullable=True)
    content_type = Column(String(30), nullable=False)
    primary_category_id = Column(Integer, nullable=False, index=True)
    category_score = Column(Float, nullable=True)
    classifier_version = Column(String(50), nullable=True)
    categorized_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_link_domain", "domain"),
        Index("idx_link_category", "primary_category_id"),
        Index("idx_link_created_at", "created_at"),
    )

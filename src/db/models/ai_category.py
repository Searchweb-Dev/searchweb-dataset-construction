"""AI 사이트 카테고리 ORM 모델."""

from sqlalchemy import Column, BigInteger, String, Boolean, ForeignKey, UniqueConstraint
from .base import BaseModel


class AICategory(BaseModel):
    """AI 사이트 카테고리 분류 (다대다)."""

    __tablename__ = "ai_category"
    __table_args__ = (
        UniqueConstraint("site_id", "level_1", "level_2", name="uq_ai_category_site_level"),
    )

    category_id = Column(BigInteger, primary_key=True, autoincrement=True,
                         comment="카테고리 고유 식별자")
    site_id = Column(BigInteger, ForeignKey("ai_site.site_id"), nullable=False, index=True,
                     comment="연결된 사이트 ID (ai_site.site_id 참조)")
    level_1 = Column(String(50), nullable=False, index=True,
                     comment="대분류 카테고리 (예: text, code, image)")
    level_2 = Column(String(100), nullable=False, index=True,
                     comment="중분류 카테고리 (예: text-generation, code-generation)")
    level_3 = Column(String(100), nullable=True,
                     comment="소분류 카테고리 (선택)")
    is_primary = Column(Boolean, nullable=False, default=False,
                        comment="대표 카테고리 여부")

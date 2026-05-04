"""AI 사이트 카테고리 ORM 모델."""

from sqlalchemy import Column, BigInteger, String, Boolean, ForeignKey, UniqueConstraint
from .base import BaseModel


class AICategory(BaseModel):
    """AI 사이트 카테고리 분류 (다대다)."""

    __tablename__ = "ai_category"
    __table_args__ = (
        UniqueConstraint("site_id", "level_1", "level_2", name="uq_ai_category_site_level"),
    )

    category_id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("ai_site.site_id"), nullable=False, index=True)
    level_1 = Column(String(50), nullable=False, index=True)
    level_2 = Column(String(100), nullable=False, index=True)
    level_3 = Column(String(100), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)

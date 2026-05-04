"""AI 사이트 태그 ORM 모델."""

from sqlalchemy import Column, BigInteger, String, ForeignKey, UniqueConstraint
from .base import BaseModel


class AITag(BaseModel):
    """AI 사이트 기능 태그 (다대다)."""

    __tablename__ = "ai_tag"
    __table_args__ = (
        UniqueConstraint("site_id", "tag_name", name="uq_ai_tag_site_name"),
    )

    tag_id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("ai_site.site_id"), nullable=False, index=True)
    tag_name = Column(String(50), nullable=False, index=True)

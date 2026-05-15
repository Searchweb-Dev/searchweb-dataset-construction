"""AI 사이트 태그 ORM 모델."""

from sqlalchemy import Column, BigInteger, String, ForeignKey, UniqueConstraint
from .base import BaseModel


class AITag(BaseModel):
    """AI 사이트 기능 태그 (다대다)."""

    __tablename__ = "ai_tag"
    __table_args__ = (
        UniqueConstraint("site_id", "tag_name", name="uq_ai_tag_site_name"),
    )

    tag_id = Column(BigInteger, primary_key=True, autoincrement=True,
                    comment="태그 고유 식별자")
    site_id = Column(BigInteger, ForeignKey("ai_site.site_id"), nullable=False, index=True,
                     comment="연결된 사이트 ID (ai_site.site_id 참조)")
    tag_name = Column(String(50), nullable=False, index=True,
                      comment="태그명 (예: 코드 생성, 번역)")

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class ExtractedURL(Base, TimestampMixin):
    """게시글 본문에서 추출/정규화된 URL을 저장하는 모델."""
    __tablename__ = "extracted_urls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    raw_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    normalized_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)

    post = relationship("Post", back_populates="urls")

    __table_args__ = (
        UniqueConstraint("post_id", "raw_url", name="uq_extracted_urls_post_raw"),
        Index("ix_extracted_urls_domain", "domain"),
    )

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models import Base, TimestampMixin, utc_now


class Post(Base, TimestampMixin):
    """키워드 검색으로 수집된 원본 게시글을 저장하는 모델."""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    platform_post_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    author_handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    urls = relationship("ExtractedURL", back_populates="post", cascade="all, delete-orphan")
    tools = relationship("ExtractedTool", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_posts_keyword", "keyword"),
        Index("ix_posts_author_handle", "author_handle"),
        Index("ix_posts_collected_at", "collected_at"),
    )

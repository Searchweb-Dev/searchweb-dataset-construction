from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """UTC 현재 시각을 반환한다."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """SQLAlchemy 선언형 모델의 공통 베이스 클래스."""
    pass


class TimestampMixin:
    """생성/수정 시각 컬럼을 공통 제공하는 믹스인."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


# Import models for metadata registration
from app.models.post import Post  # noqa: E402,F401
from app.models.tool import ExtractedTool  # noqa: E402,F401
from app.models.url import ExtractedURL  # noqa: E402,F401

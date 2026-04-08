from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ThreadPost(BaseModel):
    """파서와 저장소 레이어 사이에서 사용하는 게시글 표준 스키마."""

    platform_post_id: str
    keyword: str
    author_handle: str | None = None
    content: str | None = None
    raw_json: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

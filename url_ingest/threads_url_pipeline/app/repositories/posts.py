from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.post import Post
from app.schemas.threads import ThreadPost


class PostsRepository:
    """posts 테이블 접근을 담당하는 저장소 레이어."""

    def upsert_post(self, session: Session, data: ThreadPost) -> Post:
        """platform_post_id 기준으로 게시글을 upsert한다."""
        existing = session.execute(
            select(Post).where(Post.platform_post_id == data.platform_post_id)
        ).scalar_one_or_none()

        if existing:
            existing.keyword = data.keyword
            existing.author_handle = data.author_handle
            existing.content = data.content
            existing.raw_json = data.raw_json
            existing.collected_at = data.collected_at or datetime.now(timezone.utc)
            session.flush()
            return existing

        row = Post(
            platform_post_id=data.platform_post_id,
            keyword=data.keyword,
            author_handle=data.author_handle,
            content=data.content,
            raw_json=data.raw_json,
            collected_at=data.collected_at,
        )
        session.add(row)
        session.flush()
        return row

    def list_posts(self, session: Session, limit: int | None = None) -> Sequence[Post]:
        """ID 오름차순으로 게시글을 조회하고 필요 시 개수를 제한한다."""
        stmt = select(Post).order_by(Post.id.asc())
        if limit:
            stmt = stmt.limit(limit)
        return session.execute(stmt).scalars().all()

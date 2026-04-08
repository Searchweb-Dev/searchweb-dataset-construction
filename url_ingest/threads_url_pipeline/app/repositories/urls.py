from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.url import ExtractedURL


@dataclass(frozen=True)
class URLRecordInput:
    """URL 저장용 입력 DTO."""
    raw_url: str
    normalized_url: str
    domain: str


class URLsRepository:
    """extracted_urls 테이블 접근을 담당하는 저장소 레이어."""

    def insert_ignore_duplicates(
        self,
        session: Session,
        post_id: int,
        inputs: Iterable[URLRecordInput],
    ) -> int:
        """동일 post_id 내 raw_url 중복을 제외하고 URL 레코드를 저장한다."""
        existing_raw_urls = set(
            session.execute(select(ExtractedURL.raw_url).where(ExtractedURL.post_id == post_id)).scalars().all()
        )

        inserted = 0
        for row in inputs:
            if row.raw_url in existing_raw_urls:
                continue
            entity = ExtractedURL(
                post_id=post_id,
                raw_url=row.raw_url,
                normalized_url=row.normalized_url,
                domain=row.domain,
            )
            session.add(entity)
            inserted += 1
            existing_raw_urls.add(row.raw_url)

        session.flush()
        return inserted

    def count_for_post(self, session: Session, post_id: int) -> int:
        """특정 게시글에 저장된 URL 레코드 수를 반환한다."""
        return int(
            session.execute(
                select(func.count(ExtractedURL.id)).where(ExtractedURL.post_id == post_id)
            ).scalar_one()
        )

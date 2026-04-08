from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from app.logging import get_logger
from app.repositories.posts import PostsRepository
from app.repositories.urls import URLRecordInput, URLsRepository
from app.services.domain_normalizer import NormalizedURL, normalize_url

logger = get_logger(__name__)

# Supports http(s) and www patterns and avoids common trailing punctuation.
URL_PATTERN = re.compile(
    r"(?:(?:https?://|www\.)[^\s<>'\"()\[\]{}]+)",
    re.IGNORECASE,
)
TRAILING_PUNCTUATION = ".,;:!?)]}»”’"


def _clean_url_candidate(url: str) -> str:
    """URL 끝의 불필요한 문장부호를 제거한다."""
    cleaned = url.strip()
    while cleaned and cleaned[-1] in TRAILING_PUNCTUATION:
        cleaned = cleaned[:-1]
    return cleaned


def extract_urls_from_text(text: str | None) -> list[str]:
    """본문 텍스트에서 URL을 추출하고 순서를 유지한 채 중복을 제거한다."""

    if not text:
        return []

    found = URL_PATTERN.findall(text)
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in found:
        cleaned = _clean_url_candidate(candidate)
        if not cleaned:
            continue
        if cleaned not in seen:
            deduped.append(cleaned)
            seen.add(cleaned)
    return deduped


@dataclass
class URLExtractionStats:
    """URL 추출 단계 실행 통계를 담는 데이터 클래스."""
    processed_posts: int = 0
    extracted_urls: int = 0
    inserted_urls: int = 0
    normalize_failures: int = 0


class URLExtractionService:
    """게시글 본문 URL 추출/정규화/저장을 수행하는 서비스."""

    def __init__(
        self,
        posts_repo: PostsRepository,
        urls_repo: URLsRepository,
        subdomain_policy: str = "registered",
    ) -> None:
        """저장소와 도메인 정책을 주입받아 초기화한다."""
        self.posts_repo = posts_repo
        self.urls_repo = urls_repo
        self.subdomain_policy = subdomain_policy

    def run(self, session: Session, limit: int | None = None) -> URLExtractionStats:
        """저장된 게시글을 순회해 URL을 추출/정규화하고 DB에 반영한다."""
        stats = URLExtractionStats()
        posts = self.posts_repo.list_posts(session, limit=limit)

        for post in posts:
            stats.processed_posts += 1
            raw_urls = extract_urls_from_text(post.content)
            stats.extracted_urls += len(raw_urls)

            normalized: list[NormalizedURL] = []
            for raw_url in raw_urls:
                normalized_url = normalize_url(raw_url, subdomain_policy=self.subdomain_policy)
                if not normalized_url:
                    stats.normalize_failures += 1
                    continue
                normalized.append(normalized_url)

            inserted = self.urls_repo.insert_ignore_duplicates(
                session=session,
                post_id=post.id,
                inputs=[
                    URLRecordInput(
                        raw_url=item.raw_url,
                        normalized_url=item.normalized_url,
                        domain=item.domain,
                    )
                    for item in normalized
                ],
            )
            stats.inserted_urls += inserted

        logger.info(
            "url_extraction_done",
            extra={
                "processed_posts": stats.processed_posts,
                "extracted_urls": stats.extracted_urls,
                "inserted_urls": stats.inserted_urls,
                "normalize_failures": stats.normalize_failures,
            },
        )
        return stats

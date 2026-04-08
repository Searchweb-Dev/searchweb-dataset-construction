from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.clients.base import BaseThreadsClient
from app.logging import get_logger
from app.parsers.threads_parser import parse_threads_items
from app.repositories.posts import PostsRepository

logger = get_logger(__name__)


@dataclass
class CollectionStats:
    """수집 단계 실행 통계를 담는 데이터 클래스."""
    keywords: int = 0
    fetched_raw_items: int = 0
    parsed_posts: int = 0
    upserted_posts: int = 0


class CollectorService:
    """키워드별 게시글 수집 및 posts upsert를 수행하는 서비스."""

    def __init__(self, client: BaseThreadsClient, posts_repo: PostsRepository) -> None:
        """클라이언트와 저장소 의존성을 주입받아 초기화한다."""
        self.client = client
        self.posts_repo = posts_repo

    def collect(self, session: Session, keywords: list[str], limit_per_keyword: int = 25) -> CollectionStats:
        """키워드 목록을 순회하며 수집/파싱/upsert를 실행하고 통계를 반환한다."""
        stats = CollectionStats(keywords=len(keywords))

        for keyword in keywords:
            try:
                raw_items = self.client.search_posts(keyword=keyword, limit=limit_per_keyword)
            except Exception as exc:
                logger.exception(
                    "collect_keyword_failed",
                    extra={"keyword": keyword, "error": str(exc)},
                )
                continue

            stats.fetched_raw_items += len(raw_items)
            parsed_items = parse_threads_items(raw_items, keyword=keyword)
            stats.parsed_posts += len(parsed_items)

            for item in parsed_items:
                self.posts_repo.upsert_post(session, item)
                stats.upserted_posts += 1

            logger.info(
                "collect_keyword_done",
                extra={
                    "keyword": keyword,
                    "raw_count": len(raw_items),
                    "parsed_count": len(parsed_items),
                },
            )

        logger.info(
            "collect_done",
            extra={
                "keywords": stats.keywords,
                "fetched_raw_items": stats.fetched_raw_items,
                "parsed_posts": stats.parsed_posts,
                "upserted_posts": stats.upserted_posts,
            },
        )
        return stats

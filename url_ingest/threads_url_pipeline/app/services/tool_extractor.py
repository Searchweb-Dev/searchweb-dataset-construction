from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.logging import get_logger
from app.repositories.posts import PostsRepository
from app.repositories.tools import ToolRecordInput, ToolsRepository
from app.repositories.urls import URLsRepository

logger = get_logger(__name__)

TOOL_ALIASES: dict[str, list[str]] = {
    "Cursor": ["cursor", "커서"],
    "Perplexity": ["perplexity", "퍼플렉시티"],
    "Gamma": ["gamma", "감마"],
    "Midjourney": ["midjourney", "미드저니"],
    "Notion AI": ["notion ai", "notionai", "노션 ai", "노션ai"],
    "ChatGPT": ["chatgpt", "챗gpt", "챗지피티"],
    "Claude": ["claude", "클로드"],
}


def normalize_tool_name(name: str) -> str:
    """툴명을 소문자/공백 정규화해 비교 가능한 키로 변환한다."""
    return re.sub(r"\s+", " ", name.strip().lower())


def extract_tool_candidates(text: str | None) -> list[tuple[str, float]]:
    """사전 기반 별칭 매칭으로 툴/서비스명 후보를 추출한다."""

    if not text:
        return []
    haystack = text.lower()

    found: list[tuple[str, float]] = []
    seen: set[str] = set()
    for canonical, aliases in TOOL_ALIASES.items():
        for alias in aliases:
            pattern = r"(?<!\w)" + re.escape(alias.lower()) + r"(?!\w)"
            if re.search(pattern, haystack, flags=re.IGNORECASE):
                normalized = normalize_tool_name(canonical)
                if normalized not in seen:
                    found.append((canonical, 0.85))
                    seen.add(normalized)
                break
    return found


@dataclass
class ToolExtractionStats:
    """툴명 추출 단계 실행 통계를 담는 데이터 클래스."""
    processed_posts: int = 0
    inserted_tools: int = 0


class ToolExtractionService:
    """게시글에서 툴명 후보를 추출해 저장하는 서비스."""

    def __init__(
        self,
        posts_repo: PostsRepository,
        urls_repo: URLsRepository,
        tools_repo: ToolsRepository,
    ) -> None:
        """저장소 의존성을 주입받아 서비스를 초기화한다."""
        self.posts_repo = posts_repo
        self.urls_repo = urls_repo
        self.tools_repo = tools_repo

    def run(self, session: Session, only_without_urls: bool = True, limit: int | None = None) -> ToolExtractionStats:
        """조건에 맞는 게시글에서 툴 후보를 추출하고 중복 없이 저장한다."""
        stats = ToolExtractionStats()
        posts = self.posts_repo.list_posts(session, limit=limit)

        for post in posts:
            if only_without_urls and self.urls_repo.count_for_post(session, post.id) > 0:
                continue

            stats.processed_posts += 1
            candidates = extract_tool_candidates(post.content)
            rows = [
                ToolRecordInput(
                    tool_name=name,
                    normalized_tool_name=normalize_tool_name(name),
                    confidence=confidence,
                )
                for name, confidence in candidates
            ]
            inserted = self.tools_repo.insert_ignore_duplicates(session, post.id, rows)
            stats.inserted_tools += inserted

        logger.info(
            "tool_extraction_done",
            extra={
                "processed_posts": stats.processed_posts,
                "inserted_tools": stats.inserted_tools,
                "only_without_urls": only_without_urls,
            },
        )
        return stats

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.logging import get_logger
from app.schemas.threads import ThreadPost

logger = get_logger(__name__)


def _deep_get(item: dict[str, Any], path: str) -> Any:
    """점(.) 경로 문자열을 따라 중첩 dict 값을 안전하게 조회한다."""
    current: Any = item
    for key in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def parse_threads_item(item: dict[str, Any], keyword: str) -> ThreadPost | None:
    """
    단일 원시 응답 아이템을 ThreadPost 표준 스키마로 변환한다.

    API 필드 변동 가능성을 고려해 여러 후보 필드를 방어적으로 확인한다.
    """

    id_candidates = [
        item.get("id"),
        item.get("post_id"),
        item.get("media_id"),
        item.get("thread_id"),
    ]
    platform_post_id = next((str(value) for value in id_candidates if value), None)
    if not platform_post_id:
        logger.warning(
            "threads_parser_missing_platform_post_id",
            extra={"keyword": keyword, "raw": item},
        )
        return None

    content_candidates = [
        item.get("text"),
        item.get("content"),
        item.get("caption"),
        item.get("message"),
        _deep_get(item, "text.value"),
    ]
    content = next((str(value) for value in content_candidates if isinstance(value, str) and value.strip()), None)

    author_candidates = [
        item.get("username"),
        item.get("author_handle"),
        _deep_get(item, "author.username"),
        _deep_get(item, "user.username"),
        _deep_get(item, "user.handle"),
        _deep_get(item, "owner.username"),
    ]
    author_handle = next(
        (str(value) for value in author_candidates if isinstance(value, str) and value.strip()),
        None,
    )

    return ThreadPost(
        platform_post_id=platform_post_id,
        keyword=keyword,
        author_handle=author_handle,
        content=content,
        raw_json=item,
        collected_at=datetime.now(timezone.utc),
    )


def parse_threads_items(items: list[dict[str, Any]], keyword: str) -> list[ThreadPost]:
    """원시 아이템 리스트를 순회하며 파싱 성공 건만 모아 반환한다."""
    parsed: list[ThreadPost] = []
    for item in items:
        try:
            parsed_item = parse_threads_item(item, keyword=keyword)
            if parsed_item:
                parsed.append(parsed_item)
        except Exception as exc:
            logger.exception(
                "threads_parser_item_failed",
                extra={"keyword": keyword, "error": str(exc), "raw": item},
            )
    return parsed

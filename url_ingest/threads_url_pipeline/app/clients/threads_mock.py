from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.clients.base import BaseThreadsClient

MOCK_POSTS: list[dict[str, Any]] = [
    {
        "id": "mock_001",
        "text": "AI 서비스 추천: https://www.perplexity.ai 정말 유용합니다.",
        "username": "dev_kim",
    },
    {
        "id": "mock_002",
        "text": "요즘 생산성 툴로 www.notion.so 와 https://gamma.app 같이 씁니다.",
        "username": "pm_lee",
    },
    {
        "id": "mock_003",
        "text": "Best AI tool for writing? try https://www.jasper.ai/?utm_source=threads",
        "username": "writer_max",
    },
    {
        "id": "mock_004",
        "text": "Cursor랑 Perplexity 조합이 미쳤다. URL 없음",
        "username": "eng_park",
    },
    {
        "post_id": "mock_005",
        "content": "무료 AI 사이트 모음: http://huggingface.co, https://replicate.com",
        "author": {"username": "ai_curator"},
    },
    {
        "media_id": "mock_006",
        "caption": "Midjourney still wins for concept art. discord.com/invite/midjourney",
        "user": {"handle": "design_life"},
    },
    {
        "id": "mock_007",
        "text": "Notion AI로 회의록 정리 중. 링크는 없지만 강추.",
        "username": "ops_han",
    },
    {
        "id": "mock_008",
        "text": "Check this: https://bit.ly/4abcXYZ and also https://openai.com/chatgpt",
        "username": "global_nomad",
    },
    {
        "thread_id": "mock_009",
        "message": "AI 추천 받으면 대부분 Claude랑 ChatGPT를 말하더라.",
        "owner": {"username": "insight_bot"},
    },
    {
        "id": "mock_010",
        "text": "생산성 툴은 Linear + Notion + Cursor. https://linear.app",
        "username": "startup_j",
    },
    {
        "id": "mock_011",
        "text": "Perplexity보다 https://you.com 도 괜찮음",
        "username": "search_geek",
    },
    {
        "id": "mock_012",
        "text": "AI 툴 비교글 업데이트: https://www.futurepedia.io/?fbclid=12345",
        "username": "tool_hunter",
    },
    {
        "id": "mock_013",
        "text": "무료 AI 사이트? playgroundai.com, leonardo.ai",
        "username": "creator_cho",
    },
]


class MockThreadsClient(BaseThreadsClient):
    """고정된 로컬 샘플 데이터를 반환하는 mock 클라이언트."""

    def __init__(self, posts: list[dict[str, Any]] | None = None) -> None:
        """사용자 지정 샘플이 있으면 사용하고, 없으면 기본 MOCK_POSTS를 사용한다."""
        self._posts = posts or MOCK_POSTS

    def search_posts(self, keyword: str, limit: int = 25) -> list[dict[str, Any]]:
        """키워드를 포함하는 샘플 게시글을 필터링해 반환한다."""
        token = keyword.lower().strip()
        matched: list[dict[str, Any]] = []
        for post in self._posts:
            text = " ".join(
                str(post.get(key, "")) for key in ("text", "content", "caption", "message")
            ).lower()
            if token in text:
                matched.append(deepcopy(post))

        if not matched:
            # fallback: return a slice so end-to-end remains runnable for unknown keywords
            matched = [deepcopy(item) for item in self._posts[: min(limit, 10)]]

        return matched[:limit]

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseThreadsClient(ABC):
    """키워드 기반 게시글 검색을 위한 클라이언트 인터페이스."""

    @abstractmethod
    def search_posts(self, keyword: str, limit: int = 25) -> list[dict[str, Any]]:
        """키워드로 게시글을 조회해 원시 dict 리스트를 반환한다."""
        raise NotImplementedError

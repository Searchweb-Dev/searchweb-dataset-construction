from __future__ import annotations

from typing import Any

import httpx

from app.clients.base import BaseThreadsClient
from app.logging import get_logger

logger = get_logger(__name__)


class ThreadsApiClient(BaseThreadsClient):
    """
    실제 Threads API 호출 클라이언트.

    TODO:
    - 운영 적용 전 최신 Meta 공식 문서 기준으로 엔드포인트/파라미터를 재검증해야 한다.
    - API 응답 스키마 변경 시 이 클래스보다 파서 레이어를 우선 수정한다.
    """

    def __init__(
        self,
        base_url: str,
        search_path: str,
        access_token: str,
        search_type: str = "TOP",
        search_mode: str = "KEYWORD",
        fields: str = (
            "id,text,media_type,permalink,timestamp,username,has_replies,is_quote_post,is_reply"
        ),
        timeout_seconds: int = 20,
    ) -> None:
        """API 호출에 필요한 기본 접속 정보를 초기화한다."""
        self.base_url = base_url.rstrip("/")
        normalized_path = "/" + search_path.strip("/")
        if not normalized_path.startswith("/v"):
            normalized_path = f"/v1.0{normalized_path}"
        self.search_path = normalized_path
        self.access_token = access_token
        self.search_type = search_type
        self.search_mode = search_mode
        self.fields = fields
        self.timeout_seconds = timeout_seconds

    def search_posts(self, keyword: str, limit: int = 25) -> list[dict[str, Any]]:
        """키워드 검색 요청을 보내고 응답에서 게시글 아이템 리스트를 추출한다."""
        if not self.access_token:
            logger.error("threads_api_token_missing", extra={"keyword": keyword})
            return []

        url = f"{self.base_url}{self.search_path}"
        params = {
            "q": keyword,
            "limit": limit,
            "search_type": self.search_type,
            "search_mode": self.search_mode,
            "fields": self.fields,
            "access_token": self.access_token,
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            response_text = exc.response.text[:500] if exc.response is not None else ""
            logger.exception(
                "threads_api_request_failed",
                extra={
                    "keyword": keyword,
                    "error": str(exc),
                    "url": url,
                    "response_text": response_text,
                    "search_type": self.search_type,
                    "search_mode": self.search_mode,
                },
            )
            return []
        except Exception as exc:
            logger.exception(
                "threads_api_request_failed",
                extra={
                    "keyword": keyword,
                    "error": str(exc),
                    "url": url,
                    "search_type": self.search_type,
                    "search_mode": self.search_mode,
                },
            )
            return []

        items = self._extract_items(payload)
        logger.info(
            "threads_api_search_done",
            extra={
                "keyword": keyword,
                "fetched_count": len(items),
                "url": url,
                "search_type": self.search_type,
                "search_mode": self.search_mode,
            },
        )
        return items

    @staticmethod
    def _extract_items(payload: Any) -> list[dict[str, Any]]:
        """다양한 응답 형태에서 게시글 리스트를 방어적으로 추출한다."""
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            # Fallback for unexpected schema
            if all(isinstance(v, (str, int, float, bool, type(None), list, dict)) for v in payload.values()):
                return [payload]
        return []

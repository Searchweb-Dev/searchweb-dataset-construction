"""
평가 대상이 AI 사이트인지 판정하는 스코프 게이트 모듈.
"""

from __future__ import annotations

import re
from typing import Dict

from keywords import AI_SITE_KEYWORDS, NON_AI_SITE_KEYWORDS
from models import FetchResult
from utils import get_domain, lower


class AiScopeClassifierMixin:
    """수집 텍스트를 기반으로 AI 사이트 여부를 판정하는 믹스인."""

    def _classify_ai_scope(self, homepage: FetchResult, all_pages: Dict[str, FetchResult]) -> Dict[str, object]:
        """페이지 텍스트/링크를 결합해 AI 사이트 판정 결과를 반환한다."""
        usable_pages = [p for p in all_pages.values() if p.ok]
        page_blobs = [" ".join([p.final_url, p.title, p.meta_description, p.text[:5000]]) for p in usable_pages]
        link_blobs = [f"{t} {u}" for p in usable_pages for t, u in p.links[:80]]
        combined_blob = lower(" ".join(page_blobs + link_blobs))
        return self._infer_ai_site_scope(combined_blob, homepage)

    def _infer_ai_site_scope(self, text_blob: str, homepage: FetchResult) -> Dict[str, object]:
        """수집 텍스트를 기반으로 평가 대상이 AI 사이트인지 판별한다."""
        normalized_blob = lower(text_blob)
        ai_hits = {k for k in AI_SITE_KEYWORDS if k in normalized_blob}
        non_ai_hits = {k for k in NON_AI_SITE_KEYWORDS if k in normalized_blob}
        if re.search(r"(?<![a-z0-9])ai(?![a-z0-9])", normalized_blob):
            ai_hits.add("ai")

        domain = get_domain(homepage.final_url or homepage.url)
        known_ai_brand_hint = any(
            token in domain
            for token in [
                "openai",
                "anthropic",
                "huggingface",
                "perplexity",
                "midjourney",
                "stability",
                "mistral",
                "cohere",
            ]
        )
        tld_ai_hint = domain.endswith(".ai")

        if len(ai_hits) >= 2:
            return {
                "is_ai_site": True,
                "confidence": 0.96,
                "reason": f"AI 관련 키워드 {len(ai_hits)}개를 확인함",
                "ai_keyword_hits": sorted(ai_hits)[:8],
                "non_ai_keyword_hits": sorted(non_ai_hits)[:8],
            }
        if len(ai_hits) == 1 and len(non_ai_hits) <= 2:
            return {
                "is_ai_site": True,
                "confidence": 0.76,
                "reason": "AI 관련 핵심 키워드가 확인됨",
                "ai_keyword_hits": sorted(ai_hits)[:8],
                "non_ai_keyword_hits": sorted(non_ai_hits)[:8],
            }
        if known_ai_brand_hint and (len(ai_hits) >= 1 or len(non_ai_hits) <= 5):
            return {
                "is_ai_site": True,
                "confidence": 0.82 if len(ai_hits) >= 1 else 0.66,
                "reason": "AI 브랜드 도메인 신호가 확인됨",
                "ai_keyword_hits": sorted(ai_hits)[:8],
                "non_ai_keyword_hits": sorted(non_ai_hits)[:8],
            }
        if tld_ai_hint and len(non_ai_hits) <= 1:
            return {
                "is_ai_site": True,
                "confidence": 0.7,
                "reason": ".ai/AI 브랜드 도메인 신호가 확인됨",
                "ai_keyword_hits": sorted(ai_hits)[:8],
                "non_ai_keyword_hits": sorted(non_ai_hits)[:8],
            }
        return {
            "is_ai_site": False,
            "confidence": 0.95 if len(ai_hits) == 0 else 0.8,
            "reason": "AI 서비스 신호가 부족하거나 일반 콘텐츠/뉴스 사이트 신호가 우세함",
            "ai_keyword_hits": sorted(ai_hits)[:8],
            "non_ai_keyword_hits": sorted(non_ai_hits)[:8],
        }

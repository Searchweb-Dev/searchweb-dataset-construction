"""분석 결과를 ai-tools.json 포맷 파일로 저장하는 유틸리티."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
)
_SOURCE_PATH = os.path.join(_DATA_DIR, "ai-tools.json")


def _favicon_url(url: str) -> str:
    """URL에서 favicon 경로를 조합한다."""
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
    return ""


def _normalize_url(url: str) -> str:
    """비교용 URL 정규화 (trailing slash 제거, 소문자)."""
    return url.rstrip("/").lower()


def _output_path(checked_at: str) -> str:
    """타임스탬프를 붙인 출력 파일 경로를 반환한다."""
    timestamp = checked_at.replace("-", "").replace("T", "_").replace(":", "")[:15]
    name, ext = os.path.splitext(os.path.basename(_SOURCE_PATH))
    return os.path.join(_DATA_DIR, f"{name}_{timestamp}{ext}")


def _load_source() -> list[dict[str, Any]]:
    """원본 ai-tools.json을 읽어 반환한다. 없으면 빈 목록."""
    if not os.path.isfile(_SOURCE_PATH):
        return []
    try:
        with open(_SOURCE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [item for item in data if isinstance(item, dict)]
    except Exception as e:
        logger.error(f"원본 파일 읽기 실패: {_SOURCE_PATH} ({e})")
        return []


def _to_entry(url: str, analysis: dict[str, Any], checked_at: str) -> dict[str, Any]:
    """분석 결과 딕셔너리를 ai-tools.json 항목 형태로 변환한다."""
    categories = analysis.get("categories") or []
    primary = next((c for c in categories if c.get("is_primary")), categories[0] if categories else {})
    return {
        "name": analysis.get("title", ""),
        "desc": analysis.get("description", ""),
        "img": _favicon_url(url),
        "link": url,
        "category": primary.get("level_2") or primary.get("level_1", ""),
        "is_ai_tool": analysis.get("is_ai_tool", False),
        "tags": analysis.get("tags", []),
        "scores": analysis.get("scores", {}),
        "confidence": analysis.get("confidence", 0),
        "checked_at": checked_at,
    }


def write_batch(
    results: list[tuple[str, dict[str, Any]]],
    checked_at: Optional[str] = None,
) -> Optional[str]:
    """한 배치 분석의 결과를 원본 기반 새 파일에 한 번에 저장한다.

    원본 ai-tools.json을 베이스로 읽고, 이번 배치에서 분석된 항목을
    link 기준으로 추가하거나 갱신한 뒤 타임스탬프 파일로 저장한다.
    원본은 수정하지 않는다.

    Args:
        results: (url, analysis_dict) 튜플 목록. analysis는 detector 반환값.
        checked_at: 타임스탬프 문자열. 미지정 시 현재 UTC 시각.

    Returns:
        저장된 파일 경로. 결과가 없거나 저장 실패 시 None.
    """
    if not results:
        return None

    ts = checked_at or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_path = _output_path(ts)

    items = _load_source()
    link_index: dict[str, int] = {
        _normalize_url(str(item.get("link", ""))): i
        for i, item in enumerate(items)
        if item.get("link")
    }

    added = updated = 0
    for url, analysis in results:
        if not url:
            continue
        entry = _to_entry(url, analysis, ts)
        normalized = _normalize_url(url)
        if normalized in link_index:
            items[link_index[normalized]] = entry
            updated += 1
        else:
            link_index[normalized] = len(items)
            items.append(entry)
            added += 1

    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
            f.write("\n")
        logger.info(f"결과 파일 저장: {out_path} (추가 {added}건, 갱신 {updated}건)")
        return out_path
    except Exception as e:
        logger.error(f"결과 파일 저장 실패: {e}")
        return None

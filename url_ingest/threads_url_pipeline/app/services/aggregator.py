from __future__ import annotations

from typing import Iterable

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.tool import ExtractedTool
from app.models.url import ExtractedURL


class AggregatorService:
    """도메인/툴/키워드 집계 조회를 제공하는 서비스."""

    def get_top_domains(self, session: Session, top_n: int = 10) -> list[dict[str, object]]:
        """도메인별 언급 수와 고유 작성자 수 상위 N개를 반환한다."""
        stmt = (
            select(
                ExtractedURL.domain.label("domain"),
                func.count(ExtractedURL.id).label("mention_count"),
                func.count(distinct(Post.author_handle)).label("unique_authors"),
            )
            .join(Post, Post.id == ExtractedURL.post_id)
            .group_by(ExtractedURL.domain)
            .order_by(func.count(ExtractedURL.id).desc())
            .limit(top_n)
        )
        rows = session.execute(stmt).all()
        return [
            {
                "domain": row.domain,
                "mention_count": int(row.mention_count),
                "unique_authors": int(row.unique_authors or 0),
            }
            for row in rows
        ]

    def get_top_tools(self, session: Session, top_n: int = 10) -> list[dict[str, object]]:
        """정규화된 툴명 기준 언급 수 상위 N개를 반환한다."""
        stmt = (
            select(
                ExtractedTool.normalized_tool_name.label("tool_name"),
                func.count(ExtractedTool.id).label("mention_count"),
            )
            .group_by(ExtractedTool.normalized_tool_name)
            .order_by(func.count(ExtractedTool.id).desc())
            .limit(top_n)
        )
        rows = session.execute(stmt).all()
        return [{"tool_name": row.tool_name, "mention_count": int(row.mention_count)} for row in rows]

    def get_keyword_domain_frequency(self, session: Session, top_n: int = 20) -> list[dict[str, object]]:
        """키워드-도메인 조합별 언급 빈도 상위 N개를 반환한다."""
        stmt = (
            select(
                Post.keyword.label("keyword"),
                ExtractedURL.domain.label("domain"),
                func.count(ExtractedURL.id).label("mention_count"),
            )
            .join(Post, Post.id == ExtractedURL.post_id)
            .group_by(Post.keyword, ExtractedURL.domain)
            .order_by(func.count(ExtractedURL.id).desc())
            .limit(top_n)
        )
        rows = session.execute(stmt).all()
        return [
            {"keyword": row.keyword, "domain": row.domain, "mention_count": int(row.mention_count)}
            for row in rows
        ]


def format_console_table(headers: list[str], rows: Iterable[dict[str, object]]) -> str:
    """dict 행 데이터를 단순 ASCII 테이블 문자열로 변환한다."""
    rows_list = list(rows)
    if not rows_list:
        return "(no rows)"

    widths: dict[str, int] = {}
    for header in headers:
        widths[header] = max(len(header), *(len(str(row.get(header, ""))) for row in rows_list))

    def _line(sep: str = "+", fill: str = "-") -> str:
        """테이블 구분선 문자열을 생성한다."""
        return sep + sep.join(fill * (widths[h] + 2) for h in headers) + sep

    def _row(values: list[str]) -> str:
        """단일 행 문자열을 컬럼 폭에 맞춰 생성한다."""
        return "| " + " | ".join(value.ljust(widths[h]) for value, h in zip(values, headers)) + " |"

    parts = [_line(), _row(headers), _line()]
    for row in rows_list:
        parts.append(_row([str(row.get(h, "")) for h in headers]))
    parts.append(_line())
    return "\n".join(parts)

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tool import ExtractedTool


@dataclass(frozen=True)
class ToolRecordInput:
    """툴/서비스명 저장용 입력 DTO."""
    tool_name: str
    normalized_tool_name: str
    confidence: float


class ToolsRepository:
    """extracted_tools 테이블 접근을 담당하는 저장소 레이어."""

    def insert_ignore_duplicates(
        self,
        session: Session,
        post_id: int,
        inputs: Iterable[ToolRecordInput],
    ) -> int:
        """동일 post_id 내 normalized_tool_name 중복을 제외하고 저장한다."""
        existing_names = set(
            session.execute(
                select(ExtractedTool.normalized_tool_name).where(ExtractedTool.post_id == post_id)
            ).scalars().all()
        )

        inserted = 0
        for row in inputs:
            if row.normalized_tool_name in existing_names:
                continue
            entity = ExtractedTool(
                post_id=post_id,
                tool_name=row.tool_name,
                normalized_tool_name=row.normalized_tool_name,
                confidence=row.confidence,
            )
            session.add(entity)
            inserted += 1
            existing_names.add(row.normalized_tool_name)

        session.flush()
        return inserted

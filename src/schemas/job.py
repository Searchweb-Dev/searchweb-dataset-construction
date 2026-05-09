"""분석 작업 요청/응답 스키마."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, HttpUrl, Field

from .site import AISiteResponse


class AnalysisJobRequest(BaseModel):
    """분석 요청 스키마."""

    url: HttpUrl
    force_reanalyze: bool = False


class AnalysisJobResponse(BaseModel):
    """분석 작업 응답 스키마."""

    job_id: UUID
    url: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    result: Optional[AISiteResponse] = None

    model_config = {"from_attributes": True}


class BatchAnalysisRequest(BaseModel):
    """ai-tools.json 배치 분석 요청 스키마."""

    limit: Optional[int] = Field(
        default=None,
        gt=0,
        description="분석할 항목 수. 미입력 시 전체 대상.",
    )
    force_reanalyze: bool = False


class BatchAnalysisResponse(BaseModel):
    """ai-tools.json 배치 분석 응답 스키마."""

    total: int = Field(description="ai-tools.json 전체 항목 수")
    target: int = Field(description="이번 요청의 분석 대상 수 (limit 적용 후)")
    message: str = Field(description="배치 작업 접수 안내")

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

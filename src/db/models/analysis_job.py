"""분석 작업 ORM 모델."""

from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel


class AnalysisJob(BaseModel):
    """AI 사이트 분석 작업 기록."""

    __tablename__ = "analysis_job"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(BigInteger, ForeignKey("ai_site.site_id"), nullable=True, index=True)
    url = Column(String(2048), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    request_source = Column(String(50), nullable=True)

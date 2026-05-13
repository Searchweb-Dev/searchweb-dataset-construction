"""규칙기반 분류기 요청/응답 스키마."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, HttpUrl


class RuleClassifyRequest(BaseModel):
    """규칙기반 분류 요청 스키마."""

    url: HttpUrl


class CriterionResponse(BaseModel):
    """단일 품질 기준 판정 결과 스키마."""

    name: str
    passed: bool
    reason: str
    confidence: float
    evidence: List[Dict[str, str]] = []


class RuleClassifyResponse(BaseModel):
    """규칙기반 분류 결과 스키마."""

    site_id: Optional[int] = None
    input_url: str
    normalized_url: str
    predicted_status: str
    final_status: str
    passed_count: int
    hard_pass: bool
    total_score: Optional[float] = None
    score_breakdown: Optional[Dict[str, float]] = None
    review_required: bool
    review_reasons: List[str]
    criteria: Dict[str, CriterionResponse]
    summary: str
    extracted: Dict[str, Any] = {}

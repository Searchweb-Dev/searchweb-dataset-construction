"""링크 관련 모델."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseEntity


class Link(BaseEntity):
    """URL 대상(정규화 URL, 메타 정보, 자동분류 대표 카테고리)을 저장한다."""

    link_id: int = Field(description="링크 고유 ID")
    canonical_url: str = Field(description="정규화 URL(중복 기준)")
    original_url: str = Field(description="최초 저장된 원본 URL")
    domain: Optional[str] = Field(default=None, max_length=255, description="도메인")
    title: Optional[str] = Field(default=None, max_length=255, description="링크 제목(메타)")
    description: Optional[str] = Field(default=None, description="링크 설명(메타)")
    thumbnail_url: Optional[str] = Field(default=None, description="썸네일 URL")
    favicon_url: Optional[str] = Field(default=None, description="파비콘 URL")
    content_type: str = Field(max_length=30, description="콘텐츠 타입(link/article/video/pdf/etc)")
    primary_category_id: int = Field(description="대표 카테고리 ID")
    category_score: Optional[float] = Field(default=None, description="자동분류 점수(0~1)")
    classifier_version: Optional[str] = Field(default=None, max_length=50, description="분류기 버전")
    categorized_at: Optional[datetime] = Field(default=None, description="분류 시각")

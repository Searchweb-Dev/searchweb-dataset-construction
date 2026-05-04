"""링크 스키마."""

from datetime import datetime
from pydantic import BaseModel, Field


class LinkOut(BaseModel):
    """링크 응답."""
    link_id: int
    canonical_url: str
    original_url: str
    domain: str | None
    title: str | None
    description: str | None
    thumbnail_url: str | None
    favicon_url: str | None
    content_type: str
    primary_category_id: int
    category_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryOut(BaseModel):
    """카테고리 응답."""
    category_id: int
    category_name: str
    parent_category_id: int | None
    
    model_config = {"from_attributes": True}

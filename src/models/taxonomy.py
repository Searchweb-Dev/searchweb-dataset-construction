"""카테고리 분류 체계 모델."""

from typing import Optional

from pydantic import Field

from .base import BaseEntity


class CategoryMaster(BaseEntity):
    """링크 자동 분류에 사용하는 카테고리 마스터."""

    category_id: int = Field(description="카테고리 고유 ID")
    parent_category_id: Optional[int] = Field(default=None, description="상위 카테고리 ID(지금은 NULL 운영)")
    category_name: str = Field(max_length=80, description="카테고리 이름")
    category_level: int = Field(description="레벨(1=대분류, 2=소분류 등)")
    is_active: bool = Field(description="사용 여부")

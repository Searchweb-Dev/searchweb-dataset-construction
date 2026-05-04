"""카테고리 분류 체계 ORM 모델."""

from sqlalchemy import Column, Integer, String, Boolean, Index
from .base import BaseModel


class CategoryMaster(BaseModel):
    """링크 자동 분류에 사용하는 카테고리 마스터."""

    __tablename__ = "category_master"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    parent_category_id = Column(Integer, nullable=True, index=True)
    category_name = Column(String(80), nullable=False)
    category_level = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("idx_category_is_active", "is_active"),
        Index("idx_category_level", "category_level"),
    )

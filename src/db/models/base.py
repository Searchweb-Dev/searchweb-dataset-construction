"""공통 베이스 ORM 모델."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """모든 ORM 테이블에 공통으로 적용되는 감시 컬럼."""

    __abstract__ = True

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)
    created_by_member_id = Column(Integer, nullable=True)
    updated_by_member_id = Column(Integer, nullable=True)
    deleted_by_member_id = Column(Integer, nullable=True)

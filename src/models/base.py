"""공통 베이스 엔티티 모델."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    """모든 엔티티에 공통으로 적용되는 감시 컬럼 믹스인."""

    created_at: datetime = Field(description="생성 시각")
    updated_at: datetime = Field(description="마지막 수정 시각(UPDATE 시 갱신)")
    deleted_at: Optional[datetime] = Field(default=None, description="소프트 삭제 시각(NULL이면 미삭제)")
    created_by_member_id: Optional[int] = Field(default=None, description="생성자 사용자 ID(논리 참조)")
    updated_by_member_id: Optional[int] = Field(default=None, description="수정자 사용자 ID(논리 참조)")
    deleted_by_member_id: Optional[int] = Field(default=None, description="삭제자 사용자 ID(논리 참조)")

    model_config = {"from_attributes": True}

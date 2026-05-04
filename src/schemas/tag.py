"""태그 스키마."""

from datetime import datetime
from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    """태그 생성 요청."""
    tag_name: str = Field(..., max_length=50, description="태그 이름")


class TagOut(BaseModel):
    """태그 응답."""
    member_tag_id: int
    owner_member_id: int
    tag_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AttachTagRequest(BaseModel):
    """태그 부착 요청."""
    tag_id: int = Field(..., description="부착할 태그 ID")


class TagAttachmentOut(BaseModel):
    """태그 부착 응답."""
    member_saved_link_tag_id: int
    member_saved_link_id: int
    member_tag_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

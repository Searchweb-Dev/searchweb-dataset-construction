"""저장 링크 스키마."""

from datetime import datetime
from pydantic import BaseModel, Field


class SaveLinkRequest(BaseModel):
    """링크 저장 요청."""
    url: str = Field(..., description="저장할 URL")
    display_title: str = Field(..., max_length=255, description="표시 제목")
    folder_id: int = Field(..., description="대상 폴더 ID")
    note: str | None = Field(None, description="사용자 메모")


class SavedLinkUpdate(BaseModel):
    """저장 링크 수정 요청."""
    display_title: str | None = Field(None, max_length=255)
    note: str | None = Field(None)
    primary_category_id: int | None = Field(None)


class SavedLinkOut(BaseModel):
    """저장 링크 응답."""
    member_saved_link_id: int
    link_id: int
    member_folder_id: int
    display_title: str
    note: str | None
    primary_category_id: int | None
    category_source: str
    category_score: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

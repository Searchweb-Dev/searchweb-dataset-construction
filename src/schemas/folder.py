"""폴더 스키마."""

from datetime import datetime
from pydantic import BaseModel, Field


class FolderCreate(BaseModel):
    """폴더 생성 요청."""
    folder_name: str = Field(..., max_length=80, description="폴더 이름")
    description: str | None = Field(None, description="폴더 설명")
    parent_folder_id: int | None = Field(None, description="상위 폴더 ID")


class FolderUpdate(BaseModel):
    """폴더 수정 요청."""
    folder_name: str | None = Field(None, max_length=80)
    description: str | None = Field(None)


class FolderOut(BaseModel):
    """폴더 응답."""
    member_folder_id: int
    owner_member_id: int
    folder_name: str
    description: str | None
    parent_folder_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

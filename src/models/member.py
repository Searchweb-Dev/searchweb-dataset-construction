"""개인 폴더, 저장 링크, 태그 관련 모델."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseEntity


class MemberFolder(BaseEntity):
    """개인 사용자가 소유하는 폴더."""

    member_folder_id: int = Field(description="개인 폴더 고유 ID")
    owner_member_id: int = Field(description="개인 폴더 소유 사용자 ID")
    parent_folder_id: Optional[int] = Field(default=None, description="상위 폴더 ID(루트면 NULL)")
    folder_name: str = Field(max_length=80, description="폴더 이름")
    description: Optional[str] = Field(default=None, description="폴더 설명")


class MemberSavedLink(BaseEntity):
    """사용자가 개인 폴더에 링크를 저장한 항목."""

    member_saved_link_id: int = Field(description="개인 저장 항목 고유 ID")
    link_id: int = Field(description="대상 링크 ID")
    link_enrichment_id: Optional[int] = Field(default=None, description="자동 채우기 실행 ID")
    member_folder_id: int = Field(description="소속 개인 폴더 ID")
    display_title: str = Field(max_length=255, description="사용자 표시 제목(수정 가능)")
    note: Optional[str] = Field(default=None, description="사용자 메모")
    primary_category_id: Optional[int] = Field(default=None, description="대표 카테고리 ID(확정 값)")
    category_source: str = Field(max_length=10, description="분류 출처(system/member)")
    category_score: Optional[float] = Field(default=None, description="자동분류 점수(0~1)")


class MemberTag(BaseEntity):
    """사용자가 직접 만드는 개인 태그(단어) 마스터."""

    member_tag_id: int = Field(description="개인 태그 ID")
    owner_member_id: int = Field(description="태그 소유 사용자 ID")
    tag_name: str = Field(max_length=50, description="태그 이름")


class MemberSavedLinkTag(BaseModel):
    """저장 항목(개인)에 개인 태그를 부착한다."""

    member_saved_link_tag_id: int = Field(description="개인 저장 링크 태그 ID")
    member_saved_link_id: int = Field(description="개인 저장 항목 ID")
    member_tag_id: int = Field(description="개인 태그 ID")
    created_at: datetime = Field(description="부착 시각")

    model_config = {"from_attributes": True}


class MemberFolderTag(BaseModel):
    """개인 폴더에 개인 태그를 부착한다."""

    member_folder_tag_id: int = Field(description="개인 폴더 태그 ID")
    member_folder_id: int = Field(description="개인 폴더 ID")
    member_tag_id: int = Field(description="개인 태그 ID")
    created_at: datetime = Field(description="부착 시각")

    model_config = {"from_attributes": True}

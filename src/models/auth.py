"""인증 관련 모델(사용자, OAuth)."""

from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseEntity


class Member(BaseEntity):
    """서비스 사용자 계정 기본 정보."""

    member_id: int = Field(description="사용자 고유 ID")
    email: str = Field(max_length=255, description="이메일(로그인/알림용)")
    login_id: Optional[str] = Field(default=None, max_length=50, description="아이디 로그인용 계정명")
    password_hash: Optional[str] = Field(default=None, max_length=255, description="비밀번호 해시(소셜만이면 NULL)")
    member_name: str = Field(max_length=20, description="사용자 이름")
    job: Optional[str] = Field(default=None, max_length=20, description="직업")
    major: Optional[str] = Field(default=None, max_length=20, description="전공")
    status: str = Field(max_length=20, description="계정 상태(active/blocked)")


class OAuthMember(BaseEntity):
    """소셜 로그인(제공자/제공자 사용자키)과 내부 사용자 계정 매핑."""

    oauth_member_id: int = Field(description="소셜 연결 고유 ID")
    member_id: int = Field(description="연결된 사용자 ID")
    provider: str = Field(max_length=30, description="제공자(google, github 등)")
    provider_member_key: str = Field(max_length=255, description="제공자 내 사용자 고유키")

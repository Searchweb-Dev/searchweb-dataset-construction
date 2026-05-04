"""인증 관련 ORM 모델."""

from sqlalchemy import Column, Integer, String, UniqueConstraint, Index
from .base import BaseModel


class Member(BaseModel):
    """서비스 사용자 계정 기본 정보."""

    __tablename__ = "member"

    member_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    login_id = Column(String(50), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    member_name = Column(String(20), nullable=False)
    job = Column(String(20), nullable=True)
    major = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="active")

    __table_args__ = (
        Index("idx_member_status", "status"),
        Index("idx_member_created_at", "created_at"),
    )


class OAuthMember(BaseModel):
    """소셜 로그인 제공자와 내부 사용자 계정 매핑."""

    __tablename__ = "oauth_member"

    oauth_member_id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, nullable=False, index=True)
    provider = Column(String(30), nullable=False)
    provider_member_key = Column(String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint("provider", "provider_member_key", name="uq_oauth_provider_key"),
        Index("idx_oauth_member_id", "member_id"),
    )

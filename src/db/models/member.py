"""개인 폴더, 저장 링크, 태그 관련 ORM 모델."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, UniqueConstraint, Index, ForeignKey
from .base import BaseModel


class MemberFolder(BaseModel):
    """개인 사용자가 소유하는 폴더."""

    __tablename__ = "member_folder"

    member_folder_id = Column(Integer, primary_key=True, autoincrement=True)
    owner_member_id = Column(Integer, nullable=False, index=True)
    parent_folder_id = Column(Integer, nullable=True, index=True)
    folder_name = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_member_folder_owner", "owner_member_id"),
        Index("idx_member_folder_parent", "parent_folder_id"),
    )


class MemberSavedLink(BaseModel):
    """사용자가 개인 폴더에 저장한 링크."""

    __tablename__ = "member_saved_link"

    member_saved_link_id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(Integer, nullable=False, index=True)
    link_enrichment_id = Column(Integer, nullable=True, index=True)
    member_folder_id = Column(Integer, nullable=False, index=True)
    display_title = Column(String(255), nullable=False)
    note = Column(Text, nullable=True)
    primary_category_id = Column(Integer, nullable=True, index=True)
    category_source = Column(String(10), nullable=False)
    category_score = Column(Float, nullable=True)

    __table_args__ = (
        Index("idx_member_saved_link_folder", "member_folder_id"),
        Index("idx_member_saved_link_link", "link_id"),
    )


class MemberTag(BaseModel):
    """사용자가 직접 만드는 개인 태그."""

    __tablename__ = "member_tag"

    member_tag_id = Column(Integer, primary_key=True, autoincrement=True)
    owner_member_id = Column(Integer, nullable=False, index=True)
    tag_name = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("owner_member_id", "tag_name", name="uq_member_tag_owner_name"),
        Index("idx_member_tag_owner", "owner_member_id"),
    )


class MemberSavedLinkTag(BaseModel):
    """저장 항목(개인)에 개인 태그를 부착."""

    __tablename__ = "member_saved_link_tag"

    member_saved_link_tag_id = Column(Integer, primary_key=True, autoincrement=True)
    member_saved_link_id = Column(Integer, nullable=False, index=True)
    member_tag_id = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("member_saved_link_id", "member_tag_id", name="uq_saved_link_tag"),
        Index("idx_member_saved_link_tag_link", "member_saved_link_id"),
        Index("idx_member_saved_link_tag_tag", "member_tag_id"),
    )


class MemberFolderTag(BaseModel):
    """개인 폴더에 개인 태그를 부착."""

    __tablename__ = "member_folder_tag"

    member_folder_tag_id = Column(Integer, primary_key=True, autoincrement=True)
    member_folder_id = Column(Integer, nullable=False, index=True)
    member_tag_id = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("member_folder_id", "member_tag_id", name="uq_folder_tag"),
        Index("idx_member_folder_tag_folder", "member_folder_id"),
        Index("idx_member_folder_tag_tag", "member_tag_id"),
    )

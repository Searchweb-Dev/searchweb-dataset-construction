"""태그 CRUD."""

from sqlalchemy.orm import Session
from src.db.models.member import MemberTag, MemberSavedLinkTag


class TagCRUD:
    """태그 데이터 접근."""

    @staticmethod
    def create_tag(db: Session, owner_member_id: int, tag_name: str,
                   created_by_member_id: int | None = None) -> MemberTag:
        """태그 생성."""
        tag = MemberTag(
            owner_member_id=owner_member_id,
            tag_name=tag_name,
            created_by_member_id=created_by_member_id or owner_member_id,
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    @staticmethod
    def get_tag_by_id(db: Session, tag_id: int) -> MemberTag | None:
        """태그 조회 (ID)."""
        return db.query(MemberTag).filter(
            MemberTag.member_tag_id == tag_id,
            MemberTag.deleted_at.is_(None)
        ).first()

    @staticmethod
    def get_tags_by_owner(db: Session, owner_member_id: int) -> list[MemberTag]:
        """사용자의 모든 태그 조회."""
        return db.query(MemberTag).filter(
            MemberTag.owner_member_id == owner_member_id,
            MemberTag.deleted_at.is_(None)
        ).all()

    @staticmethod
    def attach_tag_to_link(db: Session, saved_link_id: int, tag_id: int,
                          created_by_member_id: int | None = None) -> MemberSavedLinkTag:
        """저장 링크에 태그 부착."""
        link_tag = MemberSavedLinkTag(
            member_saved_link_id=saved_link_id,
            member_tag_id=tag_id,
            created_by_member_id=created_by_member_id,
        )
        db.add(link_tag)
        db.commit()
        db.refresh(link_tag)
        return link_tag

    @staticmethod
    def detach_tag_from_link(db: Session, saved_link_id: int, tag_id: int,
                            deleted_by_member_id: int | None = None) -> bool:
        """저장 링크에서 태그 제거."""
        link_tag = db.query(MemberSavedLinkTag).filter(
            MemberSavedLinkTag.member_saved_link_id == saved_link_id,
            MemberSavedLinkTag.member_tag_id == tag_id,
            MemberSavedLinkTag.deleted_at.is_(None)
        ).first()
        
        if not link_tag:
            return False
        
        from datetime import datetime
        link_tag.deleted_at = datetime.utcnow()
        link_tag.deleted_by_member_id = deleted_by_member_id
        db.commit()
        return True

    @staticmethod
    def get_tags_by_link(db: Session, saved_link_id: int) -> list[MemberTag]:
        """저장 링크에 부착된 모든 태그 조회."""
        return db.query(MemberTag).join(
            MemberSavedLinkTag,
            MemberTag.member_tag_id == MemberSavedLinkTag.member_tag_id
        ).filter(
            MemberSavedLinkTag.member_saved_link_id == saved_link_id,
            MemberSavedLinkTag.deleted_at.is_(None),
            MemberTag.deleted_at.is_(None)
        ).all()

"""저장 링크 CRUD."""

from sqlalchemy.orm import Session
from src.db.models.member import MemberSavedLink


class SavedLinkCRUD:
    """저장 링크 데이터 접근."""

    @staticmethod
    def create(db: Session, link_id: int, member_folder_id: int, display_title: str,
               category_source: str = "member", note: str | None = None,
               primary_category_id: int | None = None, category_score: float | None = None,
               created_by_member_id: int | None = None) -> MemberSavedLink:
        """저장 링크 생성."""
        saved_link = MemberSavedLink(
            link_id=link_id,
            member_folder_id=member_folder_id,
            display_title=display_title,
            note=note,
            primary_category_id=primary_category_id,
            category_source=category_source,
            category_score=category_score,
            created_by_member_id=created_by_member_id,
        )
        db.add(saved_link)
        db.commit()
        db.refresh(saved_link)
        return saved_link

    @staticmethod
    def get_by_id(db: Session, saved_link_id: int) -> MemberSavedLink | None:
        """저장 링크 조회 (ID)."""
        return db.query(MemberSavedLink).filter(
            MemberSavedLink.member_saved_link_id == saved_link_id,
            MemberSavedLink.deleted_at.is_(None)
        ).first()

    @staticmethod
    def get_by_folder(db: Session, folder_id: int) -> list[MemberSavedLink]:
        """폴더별 저장 링크 조회."""
        return db.query(MemberSavedLink).filter(
            MemberSavedLink.member_folder_id == folder_id,
            MemberSavedLink.deleted_at.is_(None)
        ).all()

    @staticmethod
    def update(db: Session, saved_link_id: int, display_title: str | None = None,
               note: str | None = None, primary_category_id: int | None = None,
               updated_by_member_id: int | None = None) -> MemberSavedLink | None:
        """저장 링크 수정."""
        saved_link = SavedLinkCRUD.get_by_id(db, saved_link_id)
        if not saved_link:
            return None
        
        if display_title is not None:
            saved_link.display_title = display_title
        if note is not None:
            saved_link.note = note
        if primary_category_id is not None:
            saved_link.primary_category_id = primary_category_id
        if updated_by_member_id is not None:
            saved_link.updated_by_member_id = updated_by_member_id
        
        db.commit()
        db.refresh(saved_link)
        return saved_link

    @staticmethod
    def delete(db: Session, saved_link_id: int, deleted_by_member_id: int | None = None) -> bool:
        """저장 링크 소프트 삭제."""
        saved_link = SavedLinkCRUD.get_by_id(db, saved_link_id)
        if not saved_link:
            return False
        
        from datetime import datetime
        saved_link.deleted_at = datetime.utcnow()
        saved_link.deleted_by_member_id = deleted_by_member_id
        db.commit()
        return True

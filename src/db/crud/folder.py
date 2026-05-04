"""개인 폴더 CRUD."""

from sqlalchemy.orm import Session
from src.db.models.member import MemberFolder


class FolderCRUD:
    """폴더 데이터 접근."""

    @staticmethod
    def create(db: Session, owner_member_id: int, folder_name: str, 
               description: str | None = None, parent_folder_id: int | None = None) -> MemberFolder:
        """폴더 생성."""
        folder = MemberFolder(
            owner_member_id=owner_member_id,
            folder_name=folder_name,
            description=description,
            parent_folder_id=parent_folder_id,
            created_by_member_id=owner_member_id,
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def get_by_id(db: Session, folder_id: int) -> MemberFolder | None:
        """폴더 조회 (ID)."""
        return db.query(MemberFolder).filter(
            MemberFolder.member_folder_id == folder_id,
            MemberFolder.deleted_at.is_(None)
        ).first()

    @staticmethod
    def get_list(db: Session, owner_member_id: int) -> list[MemberFolder]:
        """사용자의 모든 폴더 조회."""
        return db.query(MemberFolder).filter(
            MemberFolder.owner_member_id == owner_member_id,
            MemberFolder.deleted_at.is_(None)
        ).all()

    @staticmethod
    def update(db: Session, folder_id: int, folder_name: str | None = None,
               description: str | None = None, updated_by_member_id: int | None = None) -> MemberFolder | None:
        """폴더 수정."""
        folder = FolderCRUD.get_by_id(db, folder_id)
        if not folder:
            return None
        
        if folder_name is not None:
            folder.folder_name = folder_name
        if description is not None:
            folder.description = description
        if updated_by_member_id is not None:
            folder.updated_by_member_id = updated_by_member_id
        
        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def delete(db: Session, folder_id: int, deleted_by_member_id: int | None = None) -> bool:
        """폴더 소프트 삭제."""
        folder = FolderCRUD.get_by_id(db, folder_id)
        if not folder:
            return False
        
        from datetime import datetime
        folder.deleted_at = datetime.utcnow()
        folder.deleted_by_member_id = deleted_by_member_id
        db.commit()
        return True

"""폴더 API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.db.crud.folder import FolderCRUD
from src.schemas.folder import FolderCreate, FolderUpdate, FolderOut

router = APIRouter(prefix="/api/v1/members", tags=["folders"])


@router.post("/{member_id}/folders", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(member_id: int, folder_in: FolderCreate, db: Session = Depends(get_db)):
    """폴더 생성."""
    folder = FolderCRUD.create(
        db=db,
        owner_member_id=member_id,
        folder_name=folder_in.folder_name,
        description=folder_in.description,
        parent_folder_id=folder_in.parent_folder_id,
    )
    return folder


@router.get("/{member_id}/folders", response_model=list[FolderOut])
def list_folders(member_id: int, db: Session = Depends(get_db)):
    """폴더 목록 조회."""
    folders = FolderCRUD.get_list(db, member_id)
    return folders


@router.patch("/{member_id}/folders/{folder_id}", response_model=FolderOut)
def update_folder(member_id: int, folder_id: int, folder_in: FolderUpdate, db: Session = Depends(get_db)):
    """폴더 수정."""
    folder = FolderCRUD.get_by_id(db, folder_id)
    if not folder or folder.owner_member_id != member_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="폴더를 찾을 수 없습니다")
    
    updated = FolderCRUD.update(
        db=db,
        folder_id=folder_id,
        folder_name=folder_in.folder_name,
        description=folder_in.description,
        updated_by_member_id=member_id,
    )
    return updated


@router.delete("/{member_id}/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(member_id: int, folder_id: int, db: Session = Depends(get_db)):
    """폴더 삭제."""
    folder = FolderCRUD.get_by_id(db, folder_id)
    if not folder or folder.owner_member_id != member_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="폴더를 찾을 수 없습니다")
    
    FolderCRUD.delete(db, folder_id, deleted_by_member_id=member_id)

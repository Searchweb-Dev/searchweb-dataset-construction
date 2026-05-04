"""태그 API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.db.crud.tag import TagCRUD
from src.db.crud.saved_link import SavedLinkCRUD
from src.db.crud.folder import FolderCRUD
from src.schemas.tag import TagCreate, TagOut, AttachTagRequest, TagAttachmentOut

router = APIRouter(prefix="/api/v1/members", tags=["tags"])


@router.post("/{member_id}/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(member_id: int, tag_in: TagCreate, db: Session = Depends(get_db)):
    """태그 생성."""
    tag = TagCRUD.create_tag(
        db=db,
        owner_member_id=member_id,
        tag_name=tag_in.tag_name,
        created_by_member_id=member_id,
    )
    return tag


@router.get("/{member_id}/tags", response_model=list[TagOut])
def list_tags(member_id: int, db: Session = Depends(get_db)):
    """태그 목록 조회."""
    tags = TagCRUD.get_tags_by_owner(db, member_id)
    return tags


@router.post("/{member_id}/saved_links/{saved_link_id}/tags", response_model=TagAttachmentOut, status_code=status.HTTP_201_CREATED)
def attach_tag_to_link(member_id: int, saved_link_id: int, tag_in: AttachTagRequest, db: Session = Depends(get_db)):
    """저장 링크에 태그 부착."""
    # 저장 링크 확인
    saved_link = SavedLinkCRUD.get_by_id(db, saved_link_id)
    if not saved_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="저장 링크를 찾을 수 없습니다")
    
    # 폴더 권한 확인
    folder = FolderCRUD.get_by_id(db, saved_link.member_folder_id)
    if not folder or folder.owner_member_id != member_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다")
    
    # 태그 확인
    tag = TagCRUD.get_tag_by_id(db, tag_in.tag_id)
    if not tag or tag.owner_member_id != member_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="태그를 찾을 수 없습니다")
    
    link_tag = TagCRUD.attach_tag_to_link(
        db=db,
        saved_link_id=saved_link_id,
        tag_id=tag_in.tag_id,
        created_by_member_id=member_id,
    )
    return link_tag


@router.delete("/{member_id}/saved_links/{saved_link_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_tag_from_link(member_id: int, saved_link_id: int, tag_id: int, db: Session = Depends(get_db)):
    """저장 링크에서 태그 제거."""
    # 저장 링크 확인
    saved_link = SavedLinkCRUD.get_by_id(db, saved_link_id)
    if not saved_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="저장 링크를 찾을 수 없습니다")
    
    # 폴더 권한 확인
    folder = FolderCRUD.get_by_id(db, saved_link.member_folder_id)
    if not folder or folder.owner_member_id != member_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다")
    
    success = TagCRUD.detach_tag_from_link(
        db=db,
        saved_link_id=saved_link_id,
        tag_id=tag_id,
        deleted_by_member_id=member_id,
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="태그 부착을 찾을 수 없습니다")

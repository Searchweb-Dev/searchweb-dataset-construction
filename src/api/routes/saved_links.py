"""저장 링크 API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.core.url import normalize_url, extract_domain, classify_url_type
from src.db.crud.link import LinkCRUD
from src.db.crud.saved_link import SavedLinkCRUD
from src.db.crud.folder import FolderCRUD
from src.schemas.saved_link import SaveLinkRequest, SavedLinkUpdate, SavedLinkOut

router = APIRouter(prefix="/api/v1/members", tags=["saved_links"])


@router.post("/{member_id}/saved_links", response_model=SavedLinkOut, status_code=status.HTTP_201_CREATED)
def save_link(member_id: int, link_in: SaveLinkRequest, db: Session = Depends(get_db)):
    """링크 저장 (URL 판별 포함).
    
    1. URL 정규화
    2. 기존 링크 확인
    3. 없으면 생성
    4. member_saved_link 생성
    """
    # 폴더 존재 확인
    folder = FolderCRUD.get_by_id(db, link_in.folder_id)
    if not folder or folder.owner_member_id != member_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="폴더를 찾을 수 없습니다")
    
    # URL 정규화
    canonical_url = normalize_url(link_in.url)
    domain = extract_domain(link_in.url)
    content_type = classify_url_type(link_in.url)
    
    # 기존 링크 조회
    existing_link = LinkCRUD.get_by_canonical_url(db, canonical_url)
    
    if existing_link:
        link_id = existing_link.link_id
    else:
        # 새 링크 생성
        new_link = LinkCRUD.create(
            db=db,
            canonical_url=canonical_url,
            original_url=link_in.url,
            domain=domain,
            content_type=content_type,
            primary_category_id=1,  # 기본값
        )
        link_id = new_link.link_id
    
    # 저장 링크 생성
    saved_link = SavedLinkCRUD.create(
        db=db,
        link_id=link_id,
        member_folder_id=link_in.folder_id,
        display_title=link_in.display_title,
        note=link_in.note,
        created_by_member_id=member_id,
    )
    return saved_link


@router.get("/{member_id}/folders/{folder_id}/saved_links", response_model=list[SavedLinkOut])
def list_saved_links(member_id: int, folder_id: int, db: Session = Depends(get_db)):
    """폴더별 저장 링크 조회."""
    folder = FolderCRUD.get_by_id(db, folder_id)
    if not folder or folder.owner_member_id != member_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="폴더를 찾을 수 없습니다")
    
    saved_links = SavedLinkCRUD.get_by_folder(db, folder_id)
    return saved_links


@router.patch("/{member_id}/saved_links/{saved_link_id}", response_model=SavedLinkOut)
def update_saved_link(member_id: int, saved_link_id: int, link_in: SavedLinkUpdate, db: Session = Depends(get_db)):
    """저장 링크 수정."""
    saved_link = SavedLinkCRUD.get_by_id(db, saved_link_id)
    if not saved_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="저장 링크를 찾을 수 없습니다")
    
    # 폴더 권한 확인
    folder = FolderCRUD.get_by_id(db, saved_link.member_folder_id)
    if not folder or folder.owner_member_id != member_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다")
    
    updated = SavedLinkCRUD.update(
        db=db,
        saved_link_id=saved_link_id,
        display_title=link_in.display_title,
        note=link_in.note,
        primary_category_id=link_in.primary_category_id,
        updated_by_member_id=member_id,
    )
    return updated


@router.delete("/{member_id}/saved_links/{saved_link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_link(member_id: int, saved_link_id: int, db: Session = Depends(get_db)):
    """저장 링크 삭제."""
    saved_link = SavedLinkCRUD.get_by_id(db, saved_link_id)
    if not saved_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="저장 링크를 찾을 수 없습니다")
    
    # 폴더 권한 확인
    folder = FolderCRUD.get_by_id(db, saved_link.member_folder_id)
    if not folder or folder.owner_member_id != member_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다")
    
    SavedLinkCRUD.delete(db, saved_link_id, deleted_by_member_id=member_id)

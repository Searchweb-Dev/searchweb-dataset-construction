"""링크 및 카테고리 조회 API."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.db.crud.link import LinkCRUD
from src.schemas.link import LinkOut

router = APIRouter(prefix="/api/v1", tags=["links"])


@router.get("/links/{link_id}", response_model=LinkOut)
def get_link(link_id: int, db: Session = Depends(get_db)):
    """링크 조회."""
    link = LinkCRUD.get_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="링크를 찾을 수 없습니다")
    return link


@router.get("/links", response_model=list[LinkOut])
def list_links_by_category(category_id: int = Query(...), db: Session = Depends(get_db)):
    """카테고리별 링크 조회."""
    links = LinkCRUD.get_by_category(db, category_id)
    return links

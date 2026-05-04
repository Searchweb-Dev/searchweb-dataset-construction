"""링크 CRUD."""

from sqlalchemy.orm import Session
from src.db.models.link import Link


class LinkCRUD:
    """링크 데이터 접근."""

    @staticmethod
    def get_by_canonical_url(db: Session, canonical_url: str) -> Link | None:
        """정규화 URL로 링크 조회."""
        return db.query(Link).filter(
            Link.canonical_url == canonical_url,
            Link.deleted_at.is_(None)
        ).first()

    @staticmethod
    def create(db: Session, canonical_url: str, original_url: str, domain: str | None,
               content_type: str = "webpage", primary_category_id: int = 1,
               title: str | None = None, description: str | None = None,
               thumbnail_url: str | None = None, favicon_url: str | None = None,
               category_score: float | None = None) -> Link:
        """링크 생성."""
        link = Link(
            canonical_url=canonical_url,
            original_url=original_url,
            domain=domain,
            title=title,
            description=description,
            thumbnail_url=thumbnail_url,
            favicon_url=favicon_url,
            content_type=content_type,
            primary_category_id=primary_category_id,
            category_score=category_score,
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    @staticmethod
    def get_by_id(db: Session, link_id: int) -> Link | None:
        """링크 조회 (ID)."""
        return db.query(Link).filter(
            Link.link_id == link_id,
            Link.deleted_at.is_(None)
        ).first()

    @staticmethod
    def get_by_category(db: Session, category_id: int) -> list[Link]:
        """카테고리별 링크 조회."""
        return db.query(Link).filter(
            Link.primary_category_id == category_id,
            Link.deleted_at.is_(None)
        ).all()

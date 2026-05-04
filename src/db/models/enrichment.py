"""자동 채우기 및 폴더 추천 규칙 ORM 모델."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, Index, UniqueConstraint
from .base import BaseModel


class FolderSuggestionRule(BaseModel):
    """카테고리를 기반으로 저장 폴더를 자동 추천하는 규칙."""

    __tablename__ = "folder_suggestion_rule"

    folder_suggestion_rule_id = Column(Integer, primary_key=True, autoincrement=True)
    scope_type = Column(String(10), nullable=False)
    owner_member_id = Column(Integer, nullable=True, index=True)
    team_id = Column(Integer, nullable=True, index=True)
    category_id = Column(Integer, nullable=False, index=True)
    member_folder_id = Column(Integer, nullable=True)
    team_folder_id = Column(Integer, nullable=True)
    priority = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("idx_suggestion_scope", "scope_type"),
        Index("idx_suggestion_category", "category_id"),
    )


class LinkEnrichment(BaseModel):
    """자동 채우기 실행의 메타데이터 수집, 분류, 키워드 추출 상태."""

    __tablename__ = "link_enrichment"

    link_enrichment_id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(Integer, nullable=False, index=True)
    request_url = Column(String, nullable=False)
    final_url = Column(String, nullable=True)
    fetch_status = Column(String(20), nullable=False)
    classify_status = Column(String(20), nullable=False)
    attempt_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    http_status = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    selected_site_name = Column(String(255), nullable=True)
    selected_title = Column(Text, nullable=True)
    selected_description = Column(Text, nullable=True)
    fetched_at = Column(DateTime, nullable=True)
    predicted_category_id = Column(Integer, nullable=True, index=True)
    predicted_score = Column(Float, nullable=True)
    classifier_version = Column(String(50), nullable=True)
    classified_at = Column(DateTime, nullable=True)
    keyword_extractor_version = Column(String(50), nullable=True)
    keyword_source = Column(String(30), nullable=True)
    keyword_extracted_at = Column(DateTime, nullable=True)
    suggested_member_folder_id = Column(Integer, nullable=True)
    suggested_team_folder_id = Column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_link_enrichment_link", "link_id"),
        Index("idx_link_enrichment_status", "fetch_status", "classify_status"),
    )


class LinkEnrichmentKeyword(BaseModel):
    """자동 채우기 실행 결과로 추출된 키워드."""

    __tablename__ = "link_enrichment_keyword"

    link_enrichment_keyword_id = Column(Integer, primary_key=True, autoincrement=True)
    link_enrichment_id = Column(Integer, nullable=False, index=True)
    keyword = Column(String(100), nullable=False)
    score = Column(Float, nullable=True)
    rank = Column(Integer, nullable=False)
    source = Column(String(30), nullable=True)

    __table_args__ = (
        Index("idx_enrichment_keyword_enrichment", "link_enrichment_id"),
    )


class LinkEnrichmentFeedback(BaseModel):
    """자동 채우기 추천에 대한 사용자 행동 피드백."""

    __tablename__ = "link_enrichment_feedback"

    link_enrichment_feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    link_enrichment_id = Column(Integer, nullable=False, index=True)
    member_saved_link_id = Column(Integer, nullable=True, index=True)
    action = Column(String(20), nullable=False)
    suggested_member_folder_id = Column(Integer, nullable=True)
    final_member_folder_id = Column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_enrichment_feedback_enrichment", "link_enrichment_id"),
        Index("idx_enrichment_feedback_action", "action"),
    )

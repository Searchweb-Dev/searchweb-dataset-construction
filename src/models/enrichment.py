"""자동 채우기(enrichment) 및 폴더 추천 규칙 모델."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseEntity


class FolderSuggestionRule(BaseEntity):
    """자동분류된 카테고리를 기반으로 저장 폴더를 자동 추천하기 위한 규칙."""

    folder_suggestion_rule_id: int = Field(description="폴더 추천 규칙 고유 ID")
    scope_type: str = Field(max_length=10, description="규칙 범위(member/team)")
    owner_member_id: Optional[int] = Field(default=None, description="개인 규칙 소유자(member 스코프일 때만)")
    team_id: Optional[int] = Field(default=None, description="팀 규칙 대상(team 스코프일 때만)")
    category_id: int = Field(description="적용 카테고리")
    member_folder_id: Optional[int] = Field(default=None, description="추천 개인 폴더 ID(member 스코프일 때만)")
    team_folder_id: Optional[int] = Field(default=None, description="추천 팀 폴더 ID(team 스코프일 때만)")
    priority: int = Field(description="우선순위")
    is_active: bool = Field(description="활성 여부")


class LinkEnrichment(BaseEntity):
    """자동 채우기 실행의 메타데이터 수집, 자동분류, 키워드 추출 상태·결과·오류·성능 정보."""

    link_enrichment_id: int = Field(description="자동 채우기 실행 레코드 고유 ID")
    link_id: int = Field(description="대상 링크 ID")
    request_url: str = Field(description="사용자가 입력한 원본 URL")
    final_url: Optional[str] = Field(default=None, description="리다이렉트 후 최종 URL")
    fetch_status: str = Field(max_length=20, description="메타 수집 상태(pending/running/success/failed)")
    classify_status: str = Field(max_length=20, description="자동분류 상태(pending/running/success/failed)")
    attempt_count: int = Field(description="시도 횟수")
    last_attempt_at: Optional[datetime] = Field(default=None, description="마지막 시도 시각")
    error_code: Optional[str] = Field(default=None, max_length=50, description="오류 코드(TIMEOUT, DNS_FAIL, BLOCKED 등)")
    error_message: Optional[str] = Field(default=None, description="오류 상세 메시지")
    http_status: Optional[int] = Field(default=None, description="HTTP 응답 코드")
    latency_ms: Optional[int] = Field(default=None, description="자동 채우기 처리 시간(ms)")
    selected_site_name: Optional[str] = Field(default=None, max_length=255, description="사이트명(선택된 값)")
    selected_title: Optional[str] = Field(default=None, description="제목 후보 중 선택된 최종 제목")
    selected_description: Optional[str] = Field(default=None, description="설명 후보 중 선택된 최종 설명")
    fetched_at: Optional[datetime] = Field(default=None, description="메타 수집 완료 시각")
    predicted_category_id: Optional[int] = Field(default=None, description="추천 카테고리 ID(대표 1개)")
    predicted_score: Optional[float] = Field(default=None, description="추천 신뢰도(0~1)")
    classifier_version: Optional[str] = Field(default=None, max_length=50, description="자동분류 로직/모델 버전")
    classified_at: Optional[datetime] = Field(default=None, description="분류 완료 시각")
    keyword_extractor_version: Optional[str] = Field(default=None, max_length=50, description="키워드 추출 로직/모델 버전")
    keyword_source: Optional[str] = Field(default=None, max_length=30, description="키워드 추출 입력 소스(title/description/title_description/other)")
    keyword_extracted_at: Optional[datetime] = Field(default=None, description="키워드 추출 완료 시각")
    suggested_member_folder_id: Optional[int] = Field(default=None, description="추천 개인 폴더 ID(자동지정 결과)")
    suggested_team_folder_id: Optional[int] = Field(default=None, description="추천 팀 폴더 ID(자동지정 결과)")


class LinkEnrichmentKeyword(BaseModel):
    """자동 채우기 실행 결과로 추출된 추천 키워드/해시태그를 정규화하여 저장한다."""

    link_enrichment_keyword_id: int = Field(description="추천 키워드 고유 ID")
    link_enrichment_id: int = Field(description="자동 채우기 실행 ID")
    keyword: str = Field(max_length=100, description="추천 키워드/해시태그(정규화 저장)")
    score: Optional[float] = Field(default=None, description="키워드 점수(0~1)")
    rank: int = Field(description="키워드 순위(0부터)")
    source: Optional[str] = Field(default=None, max_length=30, description="키워드 추출 입력 소스(title/description/title_description/other)")
    created_at: datetime = Field(description="생성 시각")

    model_config = {"from_attributes": True}


class LinkEnrichmentFeedback(BaseModel):
    """자동 채우기 추천 결과에 대해 사용자가 실제로 어떻게 행동했는지를 기록한다."""

    link_enrichment_feedback_id: int = Field(description="피드백 ID")
    link_enrichment_id: int = Field(description="어떤 자동채우기 결과에 대한 피드백인지")
    member_saved_link_id: Optional[int] = Field(default=None, description="저장으로 이어졌다면 연결(선택)")
    action: str = Field(max_length=20, description="사용자 행동(ACCEPT/MOVE/REJECT/IGNORE)")
    suggested_member_folder_id: Optional[int] = Field(default=None, description="당시 추천 폴더(스냅샷)")
    final_member_folder_id: Optional[int] = Field(default=None, description="최종 저장 폴더(이동/수락 결과)")
    created_at: datetime = Field(description="생성 시각")

    model_config = {"from_attributes": True}

# SearchWeb 구현 계획 (v0.3.0)

북마크/링크/폴더 관리 서비스를 위한 단계별 구현 계획.

---

## 프로젝트 규모

- **총 14개 테이블** (개인 도메인)
- **총 13개 API 엔드포인트** (CRUD 기준)
- **자동 채우기 파이프라인** (비동기 작업)

---

## Phase 1: 데이터 모델 및 DB 스키마 (1-2주)

### 1.1 Pydantic 모델 정의 ✓
- `src/models/__init__.py`
- `src/models/base.py` — BaseEntity 믹스인
- `src/models/auth.py` — Member, OAuthMember
- `src/models/taxonomy.py` — CategoryMaster
- `src/models/member.py` — MemberFolder, MemberSavedLink, MemberTag, MemberSavedLinkTag, MemberFolderTag
- `src/models/link.py` — Link
- `src/models/enrichment.py` — FolderSuggestionRule, LinkEnrichment, LinkEnrichmentKeyword, LinkEnrichmentFeedback

**검증:**
```bash
uv run python -c "from src.models import *; print('All models imported')"
uv run mypy src/models --strict
```

### 1.2 SQLAlchemy ORM 모델 정의
- `src/db/models/` 디렉토리 생성
- 각 Pydantic 모델에 대응하는 SQLAlchemy 모델 작성
- 외래키, 제약조건, 인덱스 정의

### 1.3 데이터베이스 마이그레이션
- Alembic 초기 설정
- 초기 마이그레이션 파일 생성
- PostgreSQL 스키마 생성

**검증:**
```bash
alembic upgrade head
# 데이터베이스에 모든 테이블 생성 확인
```

---

## Phase 2: 핵심 API 구현 (2-3주)

### 2.1 인증 및 사용자 관리
- `POST /api/v1/members` — 가입
- `GET /api/v1/members/{member_id}` — 조회
- `PATCH /api/v1/members/{member_id}` — 수정
- `POST /api/v1/auth/login` — 로그인
- `POST /api/v1/auth/logout` — 로그아웃

### 2.2 개인 폴더 관리
- `POST /api/v1/members/{member_id}/folders` — 폴더 생성
- `GET /api/v1/members/{member_id}/folders` — 목록 조회
- `PATCH /api/v1/members/{member_id}/folders/{folder_id}` — 수정
- `DELETE /api/v1/members/{member_id}/folders/{folder_id}` — 삭제

### 2.3 개인 저장 링크 관리
- `POST /api/v1/members/{member_id}/saved_links` — 링크 저장
- `GET /api/v1/members/{member_id}/folders/{folder_id}/saved_links` — 폴더별 링크 조회
- `PATCH /api/v1/members/{member_id}/saved_links/{saved_link_id}` — 수정
- `DELETE /api/v1/members/{member_id}/saved_links/{saved_link_id}` — 삭제

### 2.4 개인 태그 관리
- `POST /api/v1/members/{member_id}/tags` — 태그 생성
- `GET /api/v1/members/{member_id}/tags` — 태그 목록
- `POST /api/v1/members/{member_id}/saved_links/{saved_link_id}/tags` — 태그 부착
- `DELETE /api/v1/members/{member_id}/saved_links/{saved_link_id}/tags/{tag_id}` — 태그 제거

### 2.5 링크 및 카테고리 API
- `GET /api/v1/links/{link_id}` — 링크 조회
- `GET /api/v1/links` — 카테고리별 링크 조회
- `GET /api/v1/categories` — 카테고리 목록

**프레임워크:**
- FastAPI 2.0+
- SQLAlchemy 2.0+
- Pydantic v2
- python-jose (JWT 토큰)
- passlib (비밀번호 해싱)

**테스트:**
```bash
uv run pytest tests/api/ -v
```

---

## Phase 3: 자동 채우기 파이프라인 (2-3주)

### 3.1 링크 메타데이터 수집 (Fetcher)
- URL 정규화 (canonical_url)
- Playwright / httpx로 메타데이터 크롤링
- title, description, thumbnail, favicon 추출
- HTTP 상태 코드, 응답 시간 기록

### 3.2 자동 분류 (Classifier)
- 링크의 본문을 분석하여 카테고리 예측
- 신뢰도 점수 계산 (0~1)
- 분류기 버전 기록

### 3.3 키워드 추출 (Keyword Extractor)
- title, description에서 키워드/해시태그 추출
- 정규화 (중복 제거, 표준화)
- 순위, 점수 저장

### 3.4 폴더 추천 (Suggestion Engine)
- FolderSuggestionRule 기반 추천 폴더 결정
- 우선순위, 조건 매칭
- 개인/팀 스코프 구분

### 3.5 비동기 작업 처리
- Celery + Redis 큐
- `POST /api/v1/enrichments/start` — 자동 채우기 시작
- `GET /api/v1/enrichments/{enrichment_id}` — 진행 상황 조회
- Webhook / 폴링으로 완료 통지

### 3.6 피드백 수집
- `POST /api/v1/enrichments/{enrichment_id}/feedback` — 사용자 행동 기록
- 분류기 및 추천 엔진 개선용 데이터 축적

**도구:**
- Celery + Redis
- httpx / Playwright (웹 크롤링)
- 자동분류 모델 (scikit-learn / 또는 LLM API)

**테스트:**
```bash
uv run pytest tests/enrichment/ -v
```

---

## Phase 4: 팀 협업 기능 (v0.4.0, 3-4주)

### 4.1 팀 관리
- `POST /api/v1/teams` — 팀 생성
- `GET /api/v1/teams` — 팀 목록
- `PATCH /api/v1/teams/{team_id}` — 팀 수정
- `DELETE /api/v1/teams/{team_id}` — 팀 삭제

### 4.2 팀 멤버십
- `POST /api/v1/teams/{team_id}/members` — 팀원 초대
- `DELETE /api/v1/teams/{team_id}/members/{member_id}` — 팀원 제거

### 4.3 팀 폴더
- `POST /api/v1/teams/{team_id}/folders` — 팀 폴더 생성
- 권한 관리 (viewer/editor)

### 4.4 팀 저장 링크
- `POST /api/v1/teams/{team_id}/saved_links` — 팀 폴더에 링크 저장
- 팀원 간 공유

### 4.5 팀 태그
- 팀 차원의 공용 태그 마스터
- 팀 저장 링크에 부착

---

## 데이터베이스 설정

### PostgreSQL 설정
```bash
# .env 파일
DATABASE_URL=postgresql://user:password@localhost:5432/searchweb
```

### 초기 데이터 (Seed)
```python
# src/db/seed.py
# category_master 초기 데이터 로드
# 기본 카테고리 100개 이상 등록
```

---

## 배포 아키텍처

```
┌─────────────────┐
│  FastAPI App    │
├─────────────────┤
│ - Member API    │
│ - Folder API    │
│ - Link API      │
│ - Enrichment API│
└────────┬────────┘
         │
    ┌────▼─────┐
    │PostgreSQL │
    └───────────┘
    
┌─────────────────┐
│  Celery Worker  │
├─────────────────┤
│ - Fetcher       │
│ - Classifier    │
│ - Extractor     │
│ - Suggester     │
└────────┬────────┘
         │
    ┌────▼─────┐
    │  Redis    │
    └───────────┘
```

---

## 주요 고려사항

### 1. 소프트 삭제
- `deleted_at`, `deleted_by_member_id` 사용
- 쿼리 시 자동으로 `deleted_at IS NULL` 조건 추가

### 2. 동시성 제어
- 낙관적 잠금 (optimistic locking) 고려
- 충돌 시 재시도 로직

### 3. 캐싱
- 카테고리 데이터: Redis 캐싱
- 사용자 폴더 구조: 메모리 캐시

### 4. 보안
- JWT 토큰 기반 인증
- CORS 설정
- SQL Injection 방지 (ORM 사용)

### 5. 모니터링
- 자동 채우기 작업 상태 추적
- 오류율, 응답 시간 로깅
- Sentry / DataDog 연동

---

## 마일스톤

| 마일스톤 | 목표 | 예상 기간 |
|---------|------|----------|
| M1 | DB 스키마 + Pydantic 모델 | 1주 |
| M2 | 핵심 API (Member, Folder, SavedLink) | 2주 |
| M3 | 자동 채우기 파이프라인 MVP | 2주 |
| M4 | 통합 테스트 + 배포 준비 | 1주 |
| M5 | v0.4.0 (팀 협업 기능) | 3주 |

---

## 버전 정보

- **v0.3.0** (현재): 개인 도메인 완성
- **v0.4.0** (예정): 팀 협업 도메인 추가

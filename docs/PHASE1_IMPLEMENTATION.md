# Phase 1: 데이터 모델 및 DB 스키마 (완료)

## 개요

SearchWeb v0.3.0의 첫 번째 phase인 데이터 모델 및 DB 스키마 구현을 완료했습니다.

---

## 1.1 Pydantic 모델 정의 ✓

### 파일 구조
```
src/models/
├── __init__.py          # 모델 export
├── base.py             # BaseEntity 믹스인
├── auth.py             # Member, OAuthMember
├── taxonomy.py         # CategoryMaster
├── member.py           # MemberFolder, MemberSavedLink, MemberTag, MemberSavedLinkTag, MemberFolderTag
├── link.py             # Link
└── enrichment.py       # FolderSuggestionRule, LinkEnrichment, LinkEnrichmentKeyword, LinkEnrichmentFeedback
```

### 모델 목록 (8개)
- **auth.py**: Member(2), OAuthMember
- **taxonomy.py**: CategoryMaster(1)
- **member.py**: MemberFolder, MemberSavedLink, MemberTag, MemberSavedLinkTag, MemberFolderTag
- **link.py**: Link
- **enrichment.py**: FolderSuggestionRule, LinkEnrichment, LinkEnrichmentKeyword, LinkEnrichmentFeedback

### 검증 결과
```bash
✓ All Pydantic models imported successfully
✓ mypy src/models --strict: Success: no issues found in 7 source files
```

---

## 1.2 SQLAlchemy ORM 모델 정의 ✓

### 파일 구조
```
src/db/
├── __init__.py              # DB 엔진, 세션, Base 정의
└── models/
    ├── __init__.py          # ORM 모델 export
    ├── base.py             # BaseModel (공통 컬럼)
    ├── auth.py             # Member, OAuthMember ORM
    ├── taxonomy.py         # CategoryMaster ORM
    ├── member.py           # 개인 폴더/링크/태그 ORM
    ├── link.py             # Link ORM
    └── enrichment.py       # 자동 채우기 관련 ORM
```

### 구현 사항

#### 1. BaseModel (공통 컬럼)
```python
- created_at: DateTime (자동, 서버 기본값)
- updated_at: DateTime (자동, 수정 시 갱신)
- deleted_at: DateTime (소프트 삭제)
- created_by_member_id: Integer (생성자 ID)
- updated_by_member_id: Integer (수정자 ID)
- deleted_by_member_id: Integer (삭제자 ID)
```

#### 2. 테이블 (13개)
1. **member**: 사용자 기본 정보
   - PK: member_id
   - UK: email, login_id
   - 인덱스: status, created_at

2. **oauth_member**: OAuth 연결
   - PK: oauth_member_id
   - UK: (provider, provider_member_key)
   - FK: member_id

3. **category_master**: 링크 분류 카테고리
   - PK: category_id
   - FK: parent_category_id (자기참조)
   - 인덱스: is_active, category_level

4. **member_folder**: 개인 폴더
   - PK: member_folder_id
   - FK: owner_member_id, parent_folder_id (자기참조)
   - 인덱스: owner_member_id, parent_folder_id

5. **member_tag**: 개인 태그
   - PK: member_tag_id
   - UK: (owner_member_id, tag_name)
   - FK: owner_member_id

6. **link**: 링크 저장소
   - PK: link_id
   - UK: canonical_url
   - FK: primary_category_id
   - 인덱스: domain, category_id, created_at

7. **member_saved_link**: 개인 저장 항목
   - PK: member_saved_link_id
   - FK: link_id, member_folder_id, link_enrichment_id
   - 인덱스: folder_id, link_id

8. **member_saved_link_tag**: 저장 항목-태그 관계
   - PK: member_saved_link_tag_id
   - UK: (member_saved_link_id, member_tag_id)
   - FK: member_saved_link_id, member_tag_id

9. **member_folder_tag**: 폴더-태그 관계
   - PK: member_folder_tag_id
   - UK: (member_folder_id, member_tag_id)
   - FK: member_folder_id, member_tag_id

10. **folder_suggestion_rule**: 폴더 추천 규칙
    - PK: folder_suggestion_rule_id
    - FK: category_id, owner_member_id, team_id
    - 인덱스: scope_type, category_id, owner_member_id

11. **link_enrichment**: 자동 채우기 실행
    - PK: link_enrichment_id
    - FK: link_id, predicted_category_id
    - 상태: fetch_status, classify_status
    - 인덱스: link_id, (fetch_status, classify_status)

12. **link_enrichment_keyword**: 추출된 키워드
    - PK: link_enrichment_keyword_id
    - FK: link_enrichment_id
    - 인덱스: link_enrichment_id

13. **link_enrichment_feedback**: 사용자 피드백
    - PK: link_enrichment_feedback_id
    - FK: link_enrichment_id, member_saved_link_id
    - 인덱스: link_enrichment_id, action

### 검증 결과
```bash
✓ All SQLAlchemy ORM models imported successfully
✓ Tables defined: ['member', 'oauth_member', 'category_master', 'member_folder', 
  'member_saved_link', 'member_tag', 'member_saved_link_tag', 'member_folder_tag', 
  'link', 'folder_suggestion_rule', 'link_enrichment', 'link_enrichment_keyword', 
  'link_enrichment_feedback']
```

---

## 1.3 Alembic 마이그레이션 설정 ✓

### 파일 구조
```
alembic/
├── env.py                                          # 마이그레이션 환경 설정
├── script.py.mako                                  # 마이그레이션 스크립트 템플릿
├── alembic.ini                                     # Alembic 설정 파일
└── versions/
    └── 2475942fca07_init_create_all_tables.py     # 초기 마이그레이션 (333줄)
```

### 설정 내용

#### env.py 수정사항
1. **Base.metadata 연결**
   ```python
   from src.db.models.base import Base
   target_metadata = Base.metadata
   ```

2. **환경변수 DATABASE_URL 지원**
   ```python
   db_url = os.getenv("DATABASE_URL")
   if db_url:
       connectable = engine_from_config({"sqlalchemy.url": db_url}, ...)
   ```

#### alembic.ini 설정
- `sqlalchemy.url` 공백으로 설정 (env.py에서 환경변수 우선)
- 환경변수 `DATABASE_URL`로 DB 연결

#### 마이그레이션 파일 (2475942fca07_init_create_all_tables.py)
- **upgrade()**: 모든 13개 테이블 및 인덱스 생성
- **downgrade()**: 생성된 모든 객체 제거

### 사용 방법

#### 1. 환경변수 설정
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/searchweb"
```

또는 `.env` 파일 생성:
```
DATABASE_URL=postgresql://user:password@localhost:5432/searchweb
```

#### 2. 마이그레이션 업그레이드
```bash
uv run alembic upgrade head
```

#### 3. 마이그레이션 다운그레이드
```bash
uv run alembic downgrade base
```

#### 4. 현재 리비전 확인
```bash
uv run alembic current
```

#### 5. 히스토리 확인
```bash
uv run alembic history --oneline
```

---

## 검증 체크리스트 ✓

- [x] Pydantic 모델 8개 모두 import 성공
- [x] mypy strict 모드 검증 통과 (7개 파일)
- [x] SQLAlchemy ORM 모델 13개 모두 import 성공
- [x] Base.metadata에 13개 테이블 등록 확인
- [x] Alembic 초기화 완료
- [x] 초기 마이그레이션 파일 생성 (333줄)
- [x] 환경변수 DATABASE_URL 지원

---

## 다음 단계 (Phase 2)

Phase 1 완료 후 다음을 진행할 수 있습니다:

1. **PostgreSQL 설정 및 데이터베이스 생성**
   ```bash
   createdb searchweb
   export DATABASE_URL="postgresql://user:password@localhost:5432/searchweb"
   uv run alembic upgrade head
   ```

2. **초기 데이터 로드 (Seed)**
   - CategoryMaster 100개 이상 등록
   - 기본 사용자 데이터 (테스트용)

3. **Phase 2: 핵심 API 구현**
   - FastAPI 애플리케이션 구조
   - Member, Folder, SavedLink, Tag API
   - 인증 및 사용자 관리

---

## 파일 변경 요약

### 추가된 파일
- `src/db/__init__.py` - DB 엔진 및 세션 관리
- `src/db/models/__init__.py` - ORM 모델 export
- `src/db/models/base.py` - BaseModel 정의
- `src/db/models/auth.py` - Member, OAuthMember ORM
- `src/db/models/taxonomy.py` - CategoryMaster ORM
- `src/db/models/member.py` - 개인 폴더/링크/태그 ORM
- `src/db/models/link.py` - Link ORM
- `src/db/models/enrichment.py` - 자동 채우기 관련 ORM
- `alembic/` - 전체 Alembic 설정
- `alembic/versions/2475942fca07_init_create_all_tables.py` - 초기 마이그레이션
- `.env.example` - 환경변수 템플릿

### 수정된 파일
- `pyproject.toml` - SQLAlchemy, Alembic, psycopg2 의존성 추가

---

## 주요 특징

### 소프트 삭제 지원
모든 테이블이 BaseModel을 상속하여 다음을 지원합니다:
- `deleted_at`: 소프트 삭제 시각 (NULL이면 활성)
- `deleted_by_member_id`: 삭제자 ID
- 쿼리 시 자동으로 `deleted_at IS NULL` 조건 추가 가능

### 감시 컬럼 (Audit Columns)
- `created_at`, `updated_at`: 자동 시간 추적
- `created_by_member_id`, `updated_by_member_id`: 작업자 추적

### 외래키 및 제약조건
- 데이터 무결성 보장
- Unique 제약조건으로 중복 방지
- 자기참조 지원 (폴더 계층, 카테고리)

### 인덱스 최적화
- 주요 쿼리 경로에 인덱스 설정
- 상태 필드, 생성 시간 등 검색 최적화

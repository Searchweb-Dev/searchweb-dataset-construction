# Data Model

PostgreSQL 데이터베이스 스키마 정의입니다.

---

## Overview

3개의 주요 테이블로 구성:

1. **AnalysisJob** — 분석 작업 추적
2. **AISite** — 분석된 AI 사이트
3. **UserBookmark** — 사용자 북마크/폴더

---

## 1. AnalysisJob

분석 작업의 상태를 추적합니다.

### Schema

```python
class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    
    job_id = Column(String, primary_key=True)
    url = Column(String, nullable=False)
    status = Column(String)  # queued, processing, completed, failed
    site_id = Column(Integer, ForeignKey("ai_sites.id"), nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
```

### Fields

| 필드 | 타입 | 설명 | 인덱스 |
|------|------|------|--------|
| `job_id` | String (UUID) | 작업 고유 ID (PK) | ✅ |
| `url` | String | 분석 대상 URL | - |
| `status` | String | 작업 상태 (queued/processing/completed/failed) | ✅ |
| `site_id` | Integer (FK) | 분석 결과 저장된 AISite ID (완료 후 저장) | ✅ |
| `error` | String | 실패 사유 (failed 상태일 때만 저장) | - |
| `created_at` | DateTime | 작업 생성 시간 | ✅ |
| `completed_at` | DateTime | 작업 완료 시간 (완료 후 저장) | - |

### Lifecycle

```
1. 작업 요청 → AnalysisJob 생성 (status: queued)
2. Celery 처리 → status: processing
3. 분석 완료 → AISite 저장 + site_id 설정
4. 상태 업데이트 → status: completed (또는 failed)
```

---

## 2. AISite

분석된 AI 사이트 정보를 저장합니다.

### Schema

```python
class AISite(Base):
    __tablename__ = "ai_sites"
    
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, index=True)
    title = Column(String)
    
    # 계층적 카테고리
    category_level_1 = Column(String, index=True)
    category_level_2 = Column(String, index=True)
    category_level_3 = Column(String, nullable=True)
    
    # 추가 특성
    tags = Column(JSON, index=True)
    
    # 분석 결과
    is_ai_tool = Column(Boolean, default=True)
    scores = Column(JSON)
    summary = Column(String)
    screenshot_url = Column(String)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 편의 메서드
    @property
    def full_category_path(self) -> str:
        """전체 카테고리 경로 반환"""
        parts = [self.category_level_1, self.category_level_2]
        if self.category_level_3:
            parts.append(self.category_level_3)
        return " > ".join(parts)
```

### Fields

| 필드 | 타입 | 설명 | 인덱스 |
|------|------|------|--------|
| `id` | Integer | 사이트 고유 ID (PK) | ✅ |
| `url` | String | 사이트 URL (UNIQUE) | ✅ |
| `title` | String | 사이트 제목 | - |
| `category_level_1` | String | 모달리티 (text/image/video/audio/code/multimodal/data/business) | ✅ |
| `category_level_2` | String | 작업 유형 (text-generation/image-generation/etc) | ✅ |
| `category_level_3` | String | 세부 기능 (선택) | - |
| `tags` | JSON | 추가 특성 (배열) | ✅ |
| `is_ai_tool` | Boolean | AI 도구 여부 | - |
| `scores` | JSON | 평가 점수 {utility, trust, originality} | - |
| `summary` | String | 한 문장 요약 | - |
| `screenshot_url` | String | 스크린샷 URL | - |
| `created_at` | DateTime | 분석 시간 | ✅ |
| `updated_at` | DateTime | 마지막 수정 시간 | - |

### Category Fields

**level_1 예시:**
```
text, image, video, audio, code, multimodal, data, business
```

**level_2 예시 (level_1=text):**
```
text-generation, text-analysis, conversational, search-retrieval
```

**level_3 예시 (level_1=text, level_2=text-generation):**
```
content-creation, copywriting, email-generation, creative-writing
```

자세한 분류는 [CATEGORY_TAXONOMY.md](./CATEGORY_TAXONOMY.md) 참조

### Tags Examples

```json
[
  "multilingual",
  "api-available", 
  "free-tier",
  "open-source",
  "webhook",
  "fine-tuning",
  "real-time",
  "high-quality"
]
```

### Scores JSON Structure

```json
{
  "utility": 8.4,
  "trust": 7.9,
  "originality": 6.8
}
```

각 점수는 1~10 범위

### Example Row

```json
{
  "id": 1,
  "url": "https://midjourney.com",
  "title": "Midjourney",
  "category_level_1": "image",
  "category_level_2": "image-generation",
  "category_level_3": "text-to-image",
  "tags": ["api-available", "paid", "discord-integration", "high-quality"],
  "is_ai_tool": true,
  "scores": {
    "utility": 9.2,
    "trust": 8.8,
    "originality": 8.1
  },
  "summary": "텍스트 프롬프트로 고품질 이미지를 생성하는 AI 서비스",
  "screenshot_url": "https://...",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

## 3. UserBookmark

사용자가 AI 사이트를 폴더/북마크로 구성합니다.

### Schema

```python
class UserBookmark(Base):
    __tablename__ = "user_bookmarks"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    site_id = Column(Integer, ForeignKey("ai_sites.id"))
    folder_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Fields

| 필드 | 타입 | 설명 | 인덱스 |
|------|------|------|--------|
| `id` | Integer | 북마크 고유 ID (PK) | ✅ |
| `user_id` | String | 사용자 ID | ✅ |
| `site_id` | Integer (FK) | AISite ID | ✅ |
| `folder_name` | String | 폴더명 (예: "이미지 생성", "음성 변환") | - |
| `created_at` | DateTime | 북마크 추가 시간 | - |

### Example Usage

```python
# 사용자가 이미지 생성 도구들을 "이미지 생성" 폴더에 저장
user_id = "user_123"
for site_id in [1, 2, 3]:  # Midjourney, DALL-E, Stable Diffusion
    bookmark = UserBookmark(
        user_id=user_id,
        site_id=site_id,
        folder_name="이미지 생성"
    )
    db.add(bookmark)
```

---

## Relationships

```
AnalysisJob
  └─ site_id ──→ AISite.id

UserBookmark
  └─ site_id ──→ AISite.id
  └─ user_id (외부 연동)
```

---

## Indexing Strategy

**주요 인덱스 (검색 성능 최적화):**

```sql
-- URL 중복 방지 + 빠른 조회
CREATE UNIQUE INDEX idx_ai_site_url ON ai_sites(url);

-- 카테고리 필터링
CREATE INDEX idx_ai_site_category_l1 ON ai_sites(category_level_1);
CREATE INDEX idx_ai_site_category_l2 ON ai_sites(category_level_2);

-- 태그 검색
CREATE INDEX idx_ai_site_tags ON ai_sites USING gin(tags);

-- 생성 시간 정렬
CREATE INDEX idx_ai_site_created_at ON ai_sites(created_at DESC);

-- 작업 상태 조회
CREATE INDEX idx_analysis_job_status ON analysis_jobs(status);
CREATE INDEX idx_analysis_job_site_id ON analysis_jobs(site_id);

-- 사용자 북마크 조회
CREATE INDEX idx_user_bookmark_user_id ON user_bookmarks(user_id);
CREATE INDEX idx_user_bookmark_site_id ON user_bookmarks(site_id);
```

---

## Migration Notes

### Initial Setup

```python
# SQLAlchemy ORM 사용
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://user:pass@localhost/ai_sites")
Base.metadata.create_all(engine)
```

### Migrations (Alembic)

```bash
alembic init alembic
alembic revision --autogenerate -m "Create initial schema"
alembic upgrade head
```

---

## Query Examples

### 1. URL로 빠른 조회 (중복 분석 방지)

```python
site = db.query(AISite).filter_by(url="https://midjourney.com").first()
if site:
    return site  # 캐시 히트 - 분석 불필요
```

### 2. 카테고리로 필터링

```python
# 모든 이미지 생성 도구
tools = db.query(AISite).filter(
    AISite.category_level_1 == "image",
    AISite.category_level_2 == "image-generation"
).all()
```

### 3. 사용자 북마크 조회

```python
bookmarks = db.query(UserBookmark).filter_by(user_id="user_123").all()
sites = [db.query(AISite).get(b.site_id) for b in bookmarks]
```

### 4. 최신 분석 사이트

```python
latest = db.query(AISite).order_by(AISite.created_at.desc()).limit(10).all()
```

---

## Constraints

- **URL Uniqueness**: 같은 URL은 한 번만 저장
- **Referential Integrity**: site_id는 항상 유효한 AISite를 가리킴
- **Not Null**: 필수 필드는 NOT NULL 제약
- **JSON Validation**: scores, tags는 Pydantic으로 검증 후 저장

---

## Performance Considerations

- **대량 조회**: category 필터링 시 인덱스 활용
- **태그 검색**: GIN 인덱스로 배열 검색 가속화
- **중복 분석 방지**: URL unique 인덱스로 캐시 히트율 향상
- **폴더 구성**: user_id 인덱스로 사용자 북마크 빠른 조회

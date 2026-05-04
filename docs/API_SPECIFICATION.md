# AI 사이트 판별 개발 계획

Worker 시스템에서 AI 웹사이트를 분석하고 판별하는 로직 개발 계획.

---

## 프로젝트 규모

- **API 엔드포인트**: 2개 (분석 요청, 상태 조회)
- **DB 테이블**: 4개 (ai_site, analysis_job, ai_category, ai_tag)
- **비동기 작업**: Celery (Claude API 호출)
- **개발 기간**: 4-6주

---

## Phase 1: 데이터베이스 및 기본 설계 (1주)

### 1.1 ORM 모델 정의 ✓
- `src/db/models/ai_site.py` — AISite
- `src/db/models/analysis_job.py` — AnalysisJob
- `src/db/models/ai_category.py` — AICategory
- `src/db/models/ai_tag.py` — AITag

**검증:**
```bash
uv run python -c "from src.db.models import *; print('All models imported')"
```

### 1.2 DB 마이그레이션
- Alembic 초기 마이그레이션 생성
- PostgreSQL 테이블 생성

**검증:**
```bash
alembic upgrade head
# DB에 4개 테이블 확인
```

### 1.3 Pydantic 스키마 정의
- `src/schemas/job.py` — AnalysisJobRequest, AnalysisJobResponse
- `src/schemas/site.py` — AISiteResponse

---

## Phase 2: FastAPI + 기본 API (1주)

### 2.1 FastAPI 라우트 구현
- `POST /api/v1/analyze` — 분석 요청 (Job 생성)
- `GET /api/v1/jobs/{job_id}` — 상태 조회

### 2.2 의존성 및 인증
- `src/api/deps.py` — API Key 검증

### 2.3 에러 처리
- 잘못된 URL 형식 감지
- 작업 상태별 응답 정의

**테스트:**
```bash
uv run pytest tests/api/ -v
```

---

## Phase 3: Claude + MCP 통합 (2주)

### 3.1 Claude API 클라이언트
- `src/ai/analyzer.py` — Claude 호출 로직
- MCP (Playwright) 도구 설정
- 프롬프트 캐싱 활용

### 3.2 Playwright MCP 서버
- `src/ai/mcp_tools.py` — 웹사이트 렌더링 및 스크린샷

### 3.3 분석 로직
- `src/ai/detector.py` — AI 판별 로직
- Claude 응답 파싱 및 검증

**테스트:**
```bash
uv run pytest tests/ai/ -v
```

---

## Phase 4: Celery 비동기 처리 (1주)

### 4.1 Celery 앱 초기화
- `src/workers/celery_app.py` — Celery 설정
- Redis 큐 구성

### 4.2 비동기 작업 정의
- `src/workers/analyze_task.py` — 분석 작업
- 재시도 정책 (3회, 지수 백오프)
- 에러 처리 및 로깅

### 4.3 작업 상태 관리
- Job 상태 업데이트 (pending → processing → success/failed)
- 분석 시간 측정

**테스트:**
```bash
# Worker 실행
uv run celery -A src.workers.celery_app worker --loglevel=info

# 작업 모니터링
uv run celery -A src.workers.celery_app events
```

---

## Phase 5: 통합 테스트 및 최적화 (1주)

### 5.1 엔드투엔드 테스트
- API → Celery → Claude → DB 전체 흐름

### 5.2 성능 최적화
- 프롬프트 캐싱 효과 측정
- 동시 작업 처리 능력 테스트

### 5.3 배포 준비
- Docker 컨테이너 구성
- 환경 변수 설정 문서

---

## 개발 순서

1. **DB 스키마 정의** (Phase 1)
2. **API 엔드포인트** (Phase 2)
3. **Claude + MCP 통합** (Phase 3)
4. **Celery 비동기 처리** (Phase 4)
5. **통합 테스트** (Phase 5)

---

## 기술 스택

| 항목 | 기술 | 버전 |
|------|------|------|
| 웹 프레임워크 | FastAPI | 0.104+ |
| ORM | SQLAlchemy | 2.0+ |
| 데이터 검증 | Pydantic | 2.0+ |
| 데이터베이스 | PostgreSQL | 14+ |
| 캐시/큐 | Redis | 7+ |
| 비동기 작업 | Celery | 5.3+ |
| AI API | Claude | Sonnet 4.6 |
| 웹 렌더링 | Playwright (MCP) | - |

---

## 성공 기준

- ✓ API 응답 시간 < 1초 (Job 생성)
- ✓ 분석 완료 시간 < 60초 (Claude + 렌더링)
- ✓ 프롬프트 캐싱으로 토큰 절감 ≥ 80%
- ✓ 재시도 포함 성공률 > 95%
- ✓ 모든 E2E 테스트 통과

"""배포 가이드."""

# AI 웹사이트 판별 Worker 배포

## 개발 환경 설정

### 1. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일 수정:
- `ANTHROPIC_API_KEY`: Claude API 키
- `API_KEY`: API 인증 키
- `DATABASE_URL`: PostgreSQL 연결 문자열 (개발: SQLite 자동)
- `REDIS_URL`: Redis 연결 문자열

### 2. 개발 서버 실행

```bash
# 의존성 설치
uv sync

# API 서버 실행
uv run uvicorn src.main:app --reload

# 다른 터미널에서 Celery Worker 실행
uv run celery -A src.workers.celery_app worker --loglevel=info

# 다른 터미널에서 Celery Flower 실행 (모니터링)
uv run celery -A src.workers.celery_app flower
```

## 프로덕션 배포 (Docker)

### 1. 환경 변수 설정

```bash
export ANTHROPIC_API_KEY="your-api-key"
export API_KEY="your-secure-api-key"
```

### 2. Docker Compose로 실행

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api

# 마이그레이션 실행
docker-compose exec api uv run alembic upgrade head
```

### 3. API 테스트

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"url": "https://example.com", "force_reanalyze": false}'
```

### 4. 모니터링

- Flower (Celery 모니터링): http://localhost:5555
- API 문서: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/health

## 주요 엔드포인트

### 분석 요청
```
POST /api/v1/analyze
Header: x-api-key: <API_KEY>
Body: {"url": "https://example.com", "force_reanalyze": false}
Response: {"job_id": "uuid", "status": "pending", ...}
```

### 작업 상태 조회
```
GET /api/v1/jobs/{job_id}
Header: x-api-key: <API_KEY>
Response: {"status": "success", "result": {...}, ...}
```

## 데이터베이스 마이그레이션

### 새 마이그레이션 생성
```bash
uv run alembic revision --autogenerate -m "설명"
```

### 마이그레이션 적용
```bash
uv run alembic upgrade head
```

## 성능 최적화

### 프롬프트 캐싱
- Claude API의 프롬프트 캐싱으로 토큰 절감 (≥80%)
- 시스템 프롬프트는 자동으로 캐시됨

### 동시 처리
- Redis 큐로 비동기 작업 처리
- Celery Worker 수 조정 가능

### 모니터링
```bash
# Worker 상태 확인
docker-compose exec worker celery -A src.workers.celery_app inspect active

# 캐시 통계
# API 응답에 포함됨
```

## 트러블슈팅

### Redis 연결 오류
```bash
docker-compose restart redis
```

### 데이터베이스 마이그레이션 오류
```bash
docker-compose exec api uv run alembic upgrade head
```

### Playwright 렌더링 오류
```bash
docker-compose exec worker uv run playwright install chromium
```

## 보안 설정

### 프로덕션 환경
1. `.env` 파일에서 기본 비밀번호 변경
2. `API_KEY` 복잡한 값으로 설정
3. `ANTHROPIC_API_KEY` 환경 변수에서만 관리
4. PostgreSQL 사용자 비밀번호 변경
5. CORS 설정 조정

## 참고 자료

- [FastAPI 배포](https://fastapi.tiangolo.com/deployment/)
- [Celery 프로덕션](https://docs.celeryproject.io/en/stable/getting-started/brokers/)
- [Claude API 프롬프트 캐싱](https://anthropic.com/docs/build-a-claude-app/caching)

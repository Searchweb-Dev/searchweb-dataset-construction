# API Specification

Worker의 REST API 명세입니다.

---

## Overview

Worker는 다음 두 가지 엔드포인트를 제공합니다:

1. **분석 요청**: `POST /analyze` — 비동기 작업 생성
2. **작업 상태 조회**: `GET /jobs/{job_id}` — 진행 상황 및 결과 조회

---

## 1. Analyze Request

### Endpoint

```http
POST /analyze
Content-Type: application/json
```

### Request Body

```json
{
  "url": "https://example.com"
}
```

| 필드 | 타입 | 설명 | 필수 |
|------|------|------|------|
| `url` | string | 분석 대상 URL | ✅ |

### Immediate Response (202 Accepted)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

**주의:** Worker는 절대 동기적으로 분석 결과를 반환하지 않습니다. 항상 Job ID를 즉시 반환하고 비동기로 처리합니다.

---

## 2. Job Status Polling

### Endpoint

```http
GET /jobs/{job_id}
```

### Path Parameters

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `job_id` | string | 분석 작업 ID (POST /analyze 응답에서 획득) |

---

### Processing Response (200 OK)

작업이 진행 중일 때:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

---

### Completed Response (200 OK)

분석 완료:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "url": "https://example.com",
    "is_ai_tool": true,
    "category": {
      "level_1": "image",
      "level_2": "image-generation",
      "level_3": "text-to-image",
      "tags": ["realistic", "api-available", "paid"]
    },
    "scores": {
      "utility": 8.4,
      "trust": 7.9,
      "originality": 6.8
    },
    "summary": "텍스트 설명으로 고품질 이미지를 생성하는 AI 서비스",
    "screenshot_url": "https://..."
  }
}
```

---

### Failed Response (200 OK)

분석 실패:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "reason": "timeout"
}
```

**가능한 실패 사유:**
- `timeout` — 분석 시간 초과
- `navigation_error` — 웹사이트 접근 불가
- `anti_bot_detection` — 봇 탐지
- `invalid_domain` — 유효하지 않은 도메인
- `llm_failure` — LLM 처리 오류

---

## Job Status States

```
queued
  ↓
processing
  ↓
├─ completed (성공)
└─ failed (실패)
```

| 상태 | 설명 |
|------|------|
| `queued` | 작업이 큐에 대기 중 |
| `processing` | 분석 진행 중 |
| `completed` | 분석 완료 (result 필드 포함) |
| `failed` | 분석 실패 (reason 필드 포함) |

---

## Result Schema

### Category (카테고리 분류)

```json
{
  "level_1": "text | image | video | audio | code | multimodal | data | business",
  "level_2": "text-generation | text-analysis | image-generation | etc",
  "level_3": "blog-writing | realistic-image | etc (선택)",
  "tags": ["multilingual", "api-available", "free-tier"]
}
```

**참고:** 자세한 카테고리 체계는 [CATEGORY_TAXONOMY.md](./CATEGORY_TAXONOMY.md) 참조

### Scores (평가 점수)

```json
{
  "utility": 1-10,
  "trust": 1-10,
  "originality": 1-10
}
```

| 점수 | 설명 |
|------|------|
| `utility` | 실용성 (얼마나 유용한가) |
| `trust` | 신뢰도 (얼마나 믿을 만한가) |
| `originality` | 독창성 (얼마나 독창적인가) |

---

## Example Flow

### 1. 분석 요청

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://midjourney.com"}'
```

응답:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

### 2. 상태 확인 (진행 중)

```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

응답:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

### 3. 상태 확인 (완료)

```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

응답:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "url": "https://midjourney.com",
    "is_ai_tool": true,
    "category": {
      "level_1": "image",
      "level_2": "image-generation",
      "level_3": "text-to-image",
      "tags": ["api-available", "paid", "high-quality"]
    },
    "scores": {
      "utility": 9.2,
      "trust": 8.8,
      "originality": 8.1
    },
    "summary": "텍스트 프롬프트로 고품질 이미지를 생성하는 AI 서비스",
    "screenshot_url": "https://..."
  }
}
```

---

## Polling Recommendations

- **초기 폴링 간격**: 2초
- **최대 폴링 간격**: 10초 (exponential backoff)
- **최대 대기 시간**: 5분
- **타임아웃 후 동작**: 작업 실패로 처리

---

## Error Responses

### 400 Bad Request

```json
{
  "error": "Invalid URL format",
  "details": "url field is required"
}
```

### 404 Not Found

```json
{
  "error": "Job not found",
  "job_id": "invalid-job-id"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "details": "Please try again later"
}
```

---

## Integration Notes

- Worker는 **stateless**이므로 여러 인스턴스 배포 가능
- Job 상태는 Redis 및 PostgreSQL에 저장
- 결과는 분석 완료 후 PostgreSQL에 영구 저장
- 같은 URL에 대한 중복 분석은 DB 캐시 활용 (API 호출 불필요)

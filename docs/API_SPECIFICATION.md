# Worker API 명세

Spring Backend와 통신하는 AI 사이트 분석 Worker의 REST API.

---

## 기본 정보

- **Base URL**: `http://localhost:8000/api/v1` (로컬) / 배포 환경별
- **인증**: API Key (header: `X-API-Key`)
- **응답 형식**: JSON
- **타임아웃**: 30초

---

## 1. 분석 요청

URL을 전송하여 비동기 분석 작업을 시작합니다.

### Endpoint
```
POST /analyze
```

### Request

**Header:**
```
X-API-Key: {api_key}
Content-Type: application/json
```

**Body:**
```json
{
  "url": "https://www.example-ai-tool.com",
  "force_reanalyze": false
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `url` | string | ✓ | 분석할 웹사이트 URL |
| `force_reanalyze` | boolean | - | 기존 결과 무시하고 재분석 (기본: false) |

### Response

**Status: 202 Accepted**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://www.example-ai-tool.com",
  "status": "pending",
  "created_at": "2026-05-04T10:30:00Z",
  "started_at": null,
  "completed_at": null,
  "retry_count": 0,
  "error_message": null
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `job_id` | uuid | 분석 작업 ID (상태 조회용) |
| `url` | string | 분석 대상 URL |
| `status` | string | 작업 상태 (`pending`, `processing`, `success`, `failed`) |
| `created_at` | ISO 8601 | 작업 생성 시각 |
| `started_at` | ISO 8601 \| null | 작업 시작 시각 |
| `completed_at` | ISO 8601 \| null | 작업 완료 시각 |
| `retry_count` | integer | 재시도 횟수 |
| `error_message` | string \| null | 오류 메시지 |

### Errors

**Status: 400 Bad Request**
```json
{
  "detail": "Invalid URL format"
}
```

**Status: 429 Too Many Requests**
```json
{
  "detail": "Rate limit exceeded. Try again after 60 seconds."
}
```

---

## 2. 분석 상태 조회

작업 ID로 분석 진행 상황 및 결과를 조회합니다.

### Endpoint
```
GET /jobs/{job_id}
```

### Request

**Header:**
```
X-API-Key: {api_key}
```

### Response (진행 중)

**Status: 200 OK**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://www.example-ai-tool.com",
  "status": "processing",
  "created_at": "2026-05-04T10:30:00Z",
  "started_at": "2026-05-04T10:31:00Z",
  "completed_at": null,
  "retry_count": 0,
  "error_message": null,
  "result": null
}
```

### Response (완료)

**Status: 200 OK**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://www.example-ai-tool.com",
  "status": "success",
  "created_at": "2026-05-04T10:30:00Z",
  "started_at": "2026-05-04T10:31:00Z",
  "completed_at": "2026-05-04T10:35:00Z",
  "retry_count": 0,
  "error_message": null,
  "result": {
    "site_id": 42,
    "url": "https://www.example-ai-tool.com",
    "is_ai_tool": true,
    "title": "Example AI Tool",
    "description": "AI 기반 콘텐츠 생성 서비스",
    "categories": [
      {
        "level_1": "text",
        "level_2": "text-generation",
        "level_3": "blog-writing",
        "is_primary": true
      }
    ],
    "tags": [
      "api-available",
      "free-tier",
      "multilingual"
    ],
    "scores": {
      "utility": 8,
      "trust": 7,
      "originality": 9
    },
    "analyzer": "gemini",
    "last_analyzed_at": "2026-05-04T10:35:00Z"
  }
}
```

**result 객체 필드:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `site_id` | integer | 사이트 ID |
| `url` | string | 분석 대상 URL |
| `is_ai_tool` | boolean | AI 도구 여부 |
| `title` | string \| null | 사이트 제목 |
| `description` | string \| null | 사이트 설명 |
| `categories` | array | 카테고리 분류 목록 |
| `tags` | array | 기능 태그 목록 |
| `scores` | object | 점수 (`utility`, `trust`, `originality`, 각 1-10) |
| `analyzer` | string \| null | 분석에 사용된 도구 (`gemini`, `claude` 등) |
| `last_analyzed_at` | ISO 8601 \| null | 마지막 분석 시각 |

### Response (실패)

**Status: 200 OK**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://www.example-ai-tool.com",
  "status": "failed",
  "created_at": "2026-05-04T10:30:00Z",
  "started_at": "2026-05-04T10:31:00Z",
  "completed_at": "2026-05-04T10:35:00Z",
  "retry_count": 2,
  "error_message": "분석 실패",
  "result": null
}
```

### Errors

**Status: 404 Not Found**
```json
{
  "detail": "Job not found"
}
```

---

## 상태 값

| 상태 | 설명 |
|------|------|
| `pending` | 큐에 대기 중 |
| `processing` | 분석 진행 중 |
| `success` | 분석 완료 |
| `failed` | 분석 실패 |

---

## 에러 처리

### 재시도 정책

- 최대 3회 재시도
- 지수 백오프: 30초, 60초, 120초
- 반복 가능한 오류만 재시도 (네트워크, 타임아웃)

### 일반적인 오류

| 오류 | HTTP 상태 | 설명 |
|------|----------|------|
| Invalid URL | 400 | URL 형식 오류 |
| Rate Limited | 429 | 요청 한도 초과 |
| Server Error | 500 | 내부 서버 오류 |

---

## 예제

### cURL
```bash
# 분석 요청
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example-ai-tool.com"}'

# 상태 조회
curl -X GET http://localhost:8000/api/v1/jobs/{job_id} \
  -H "X-API-Key: your-api-key"
```

### Python (requests)
```python
import requests

api_key = "your-api-key"
headers = {"X-API-Key": api_key}

# 분석 요청
response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    headers=headers,
    json={"url": "https://www.example-ai-tool.com"}
)
job_id = response.json()["job_id"]

# 상태 조회
response = requests.get(
    f"http://localhost:8000/api/v1/jobs/{job_id}",
    headers=headers
)
print(response.json())
```

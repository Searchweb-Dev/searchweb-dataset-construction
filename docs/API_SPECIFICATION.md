# SearchWeb API 명세 (v0.3.0)

북마크/링크/폴더 관리 서비스 REST API.

---

## 기본 정보

- **Base URL**: `/api/v1`
- **인증**: Bearer Token (JWT 예정)
- **응답 형식**: JSON
- **주요 도메인**: member, folder, saved_link, link, enrichment

---

## Member (사용자) API

### 사용자 가입
```
POST /members
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "login_id": "user123",
  "password": "encrypted_password",
  "member_name": "홍길동",
  "job": "개발자",
  "major": "컴퓨터공학"
}
```

**Response (201):**
```json
{
  "member_id": 1,
  "email": "user@example.com",
  "member_name": "홍길동",
  "status": "active",
  "created_at": "2026-05-03T10:30:00Z"
}
```

### 사용자 조회
```
GET /members/{member_id}
```

**Response (200):**
```json
{
  "member_id": 1,
  "email": "user@example.com",
  "member_name": "홍길동",
  "job": "개발자",
  "major": "컴퓨터공학",
  "status": "active",
  "created_at": "2026-05-03T10:30:00Z",
  "updated_at": "2026-05-03T10:30:00Z"
}
```

### 사용자 정보 수정
```
PATCH /members/{member_id}
```

**Request Body:**
```json
{
  "member_name": "홍길동",
  "job": "시니어 개발자",
  "major": "데이터공학"
}
```

---

## Member Folder (개인 폴더) API

### 폴더 생성
```
POST /members/{member_id}/folders
```

**Request Body:**
```json
{
  "folder_name": "AI 도구",
  "parent_folder_id": null,
  "description": "유용한 AI 도구 모음"
}
```

**Response (201):**
```json
{
  "member_folder_id": 1,
  "owner_member_id": 1,
  "folder_name": "AI 도구",
  "parent_folder_id": null,
  "description": "유용한 AI 도구 모음",
  "created_at": "2026-05-03T10:30:00Z"
}
```

### 폴더 목록 조회
```
GET /members/{member_id}/folders
```

**Query Parameters:**
- `parent_folder_id`: 상위 폴더 ID (선택, null이면 루트 폴더만)

**Response (200):**
```json
{
  "items": [
    {
      "member_folder_id": 1,
      "folder_name": "AI 도구",
      "parent_folder_id": null,
      "created_at": "2026-05-03T10:30:00Z"
    },
    {
      "member_folder_id": 2,
      "folder_name": "이미지 생성",
      "parent_folder_id": 1,
      "created_at": "2026-05-03T11:00:00Z"
    }
  ],
  "total": 2
}
```

### 폴더 수정
```
PATCH /members/{member_id}/folders/{folder_id}
```

### 폴더 삭제
```
DELETE /members/{member_id}/folders/{folder_id}
```

---

## Member Saved Link (개인 저장 링크) API

### 링크 저장
```
POST /members/{member_id}/saved_links
```

**Request Body:**
```json
{
  "link_id": 1,
  "member_folder_id": 1,
  "display_title": "Midjourney - 이미지 생성 AI",
  "note": "가입 필요, Discord 연동",
  "primary_category_id": 5,
  "category_source": "system"
}
```

**Response (201):**
```json
{
  "member_saved_link_id": 1,
  "link_id": 1,
  "member_folder_id": 1,
  "display_title": "Midjourney - 이미지 생성 AI",
  "note": "가입 필요, Discord 연동",
  "primary_category_id": 5,
  "category_source": "system",
  "category_score": 0.95,
  "created_at": "2026-05-03T10:30:00Z"
}
```

### 폴더별 저장 링크 조회
```
GET /members/{member_id}/folders/{folder_id}/saved_links
```

**Query Parameters:**
- `category_id`: 카테고리 필터 (선택)
- `tag_id`: 태그 필터 (선택)
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지 크기 (기본값: 20)

**Response (200):**
```json
{
  "items": [
    {
      "member_saved_link_id": 1,
      "display_title": "Midjourney",
      "link": {
        "link_id": 1,
        "canonical_url": "https://midjourney.com",
        "title": "Midjourney",
        "domain": "midjourney.com",
        "primary_category_id": 5
      },
      "primary_category_id": 5,
      "created_at": "2026-05-03T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

### 저장 링크 수정
```
PATCH /members/{member_id}/saved_links/{saved_link_id}
```

**Request Body:**
```json
{
  "display_title": "수정된 제목",
  "note": "수정된 메모",
  "primary_category_id": 6
}
```

### 저장 링크 삭제
```
DELETE /members/{member_id}/saved_links/{saved_link_id}
```

---

## Member Tag (개인 태그) API

### 태그 생성
```
POST /members/{member_id}/tags
```

**Request Body:**
```json
{
  "tag_name": "추천"
}
```

**Response (201):**
```json
{
  "member_tag_id": 1,
  "owner_member_id": 1,
  "tag_name": "추천",
  "created_at": "2026-05-03T10:30:00Z"
}
```

### 태그 목록 조회
```
GET /members/{member_id}/tags
```

### 저장 링크에 태그 부착
```
POST /members/{member_id}/saved_links/{saved_link_id}/tags
```

**Request Body:**
```json
{
  "member_tag_id": 1
}
```

### 저장 링크에서 태그 제거
```
DELETE /members/{member_id}/saved_links/{saved_link_id}/tags/{tag_id}
```

---

## Link (링크) API

### 링크 조회
```
GET /links/{link_id}
```

**Response (200):**
```json
{
  "link_id": 1,
  "canonical_url": "https://midjourney.com",
  "original_url": "https://midjourney.com/home",
  "domain": "midjourney.com",
  "title": "Midjourney",
  "description": "AI 이미지 생성 도구",
  "thumbnail_url": "https://...",
  "favicon_url": "https://...",
  "content_type": "link",
  "primary_category_id": 5,
  "category_score": 0.95,
  "classifier_version": "v1.0",
  "categorized_at": "2026-05-03T10:30:00Z",
  "created_at": "2026-05-03T10:30:00Z"
}
```

### 카테고리별 링크 조회
```
GET /links
```

**Query Parameters:**
- `category_id`: 카테고리 ID
- `domain`: 도메인 필터 (선택)
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지 크기 (기본값: 20)

---

## Link Enrichment (자동 채우기) API

### 자동 채우기 시작
```
POST /enrichments/start
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "member_id": 1
}
```

**Response (202 Accepted):**
```json
{
  "link_enrichment_id": 1,
  "link_id": 1,
  "request_url": "https://example.com",
  "fetch_status": "pending",
  "classify_status": "pending",
  "created_at": "2026-05-03T10:30:00Z"
}
```

### 자동 채우기 상태 조회
```
GET /enrichments/{enrichment_id}
```

**Response (200):**
```json
{
  "link_enrichment_id": 1,
  "link_id": 1,
  "request_url": "https://example.com",
  "final_url": "https://example.com/home",
  "fetch_status": "success",
  "classify_status": "success",
  "attempt_count": 1,
  "error_code": null,
  "selected_title": "Example",
  "selected_description": "Example website",
  "predicted_category_id": 5,
  "predicted_score": 0.92,
  "classifier_version": "v1.0",
  "suggested_member_folder_id": 1,
  "created_at": "2026-05-03T10:30:00Z",
  "classified_at": "2026-05-03T10:31:00Z"
}
```

### 자동 채우기 결과에 피드백 제출
```
POST /enrichments/{enrichment_id}/feedback
```

**Request Body:**
```json
{
  "action": "ACCEPT",
  "member_saved_link_id": 1,
  "final_member_folder_id": 1
}
```

**응답 (200):**
```json
{
  "link_enrichment_feedback_id": 1,
  "link_enrichment_id": 1,
  "action": "ACCEPT",
  "member_saved_link_id": 1,
  "final_member_folder_id": 1,
  "created_at": "2026-05-03T10:32:00Z"
}
```

**피드백 액션 종류:**
- `ACCEPT`: 추천된 폴더에 저장 수락
- `MOVE`: 추천된 폴더에서 다른 폴더로 이동
- `REJECT`: 추천 거절 후 저장 안 함
- `IGNORE`: 무시 (저장하지 않음)

---

## Category (카테고리) API

### 카테고리 목록 조회
```
GET /categories
```

**Query Parameters:**
- `level`: 카테고리 레벨 필터 (1, 2 등)
- `parent_id`: 상위 카테고리 ID (선택)
- `is_active`: 활성 여부 필터 (기본값: true)

**Response (200):**
```json
{
  "items": [
    {
      "category_id": 1,
      "category_name": "문서",
      "category_level": 1,
      "is_active": true
    },
    {
      "category_id": 2,
      "category_name": "이미지",
      "category_level": 1,
      "is_active": true
    }
  ],
  "total": 2
}
```

---

## Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력 값이 유효하지 않습니다.",
    "details": {
      "email": "유효한 이메일 주소를 입력하세요."
    }
  }
}
```

---

## Pagination

리스트 응답은 다음 형식을 따릅니다:

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "has_next": true,
  "has_prev": false
}
```

---

## Status Codes

| 코드 | 의미 |
|------|------|
| 200 | 성공 |
| 201 | 생성됨 |
| 202 | 수락됨 (비동기 처리) |
| 400 | 잘못된 요청 |
| 401 | 인증 필요 |
| 403 | 접근 권한 없음 |
| 404 | 찾을 수 없음 |
| 409 | 충돌 (중복 등) |
| 500 | 서버 오류 |

---

## Rate Limiting

- 기본 한도: 분당 100 요청
- 응답 헤더: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 버전 정보

- **v0.3.0** (현재): 개인 도메인 API 완성
- **v0.4.0** (예정): 팀 협업 API 추가

# ARCHITECTURE.md

# AI Website Evaluation Worker Architecture

## Overview

이 프로젝트는 URL을 입력받아 웹사이트를 분석하고,
해당 사이트가 유용한 AI 서비스인지 판별하는 **AI 사이트 분석 Worker** 시스템이다.

Spring Backend와 분리되어 독립적으로 동작하며,
다음 기능을 담당한다:

- FastAPI 기반 비동기 API (Spring Backend와 통신)
- Celery를 통한 비동기 분석 작업 처리
- **Claude API + MCP (Model Context Protocol) 통합**
- Playwright로 웹사이트 렌더링 및 콘텐츠 추출
- Claude를 통한 AI 사이트 판별 (판별, 분류, 점수화, 요약)
- 분석 결과 저장 (PostgreSQL)
- 분석 상태 관리 (Redis)

---

# High Level Architecture (MCP 방식)

```text
+---------------------------+
| Spring Backend            |
|---------------------------|
| API / Auth / DB           |
+----------+----------------+
           |
           | POST /analyze?url=...
           v
+---------------------------+
| FastAPI Worker API        |
|---------------------------|
| - Job 생성                 |
| - Job ID 즉시 반환         |
+----------+----------------+
           |
           | enqueue
           v
+---------------------------+
| Redis Queue (Celery)      |
|---------------------------|
| - 작업 큐                  |
| - Job 상태 저장소          |
+----------+----------------+
           |
           v
+---------------------------+
| Celery Worker Process     |
|---------------------------|
| ┌──────────────────────┐ |
| │ MCP Server           │ |
| │ (Playwright도구 제공) │ |
| └──────────────────────┘ |
| ┌──────────────────────┐ |
| │ Claude API (+ MCP)   │ |
| │ (분석 수행)          │ |
| └──────────────────────┘ |
| ┌──────────────────────┐ |
| │ Pydantic Validator   │ |
| │ (결과 정규화)        │ |
| └──────────────────────┘ |
+----------+----------------+
           |
           | 결과 저장
           v
+---------------------------+
| PostgreSQL Database       |
|---------------------------|
| - AnalysisJob            |
| - AISite                 |
| - UserBookmark           |
+---------------------------+
```

---

# Responsibilities

## Spring Backend

Spring Backend는 다음 역할만 담당한다.

- 사용자 요청 처리
- 인증/인가
- Job 요청 전달
- Job 상태 조회
- 최종 결과 저장 및 제공

Worker 내부 구현에는 관여하지 않는다.

---

## Python Worker

Worker는 AI 분석 전용 서비스다.

주요 역할:

- 사이트 렌더링
- DOM 추출
- Screenshot 생성
- LLM 분석
- 결과 구조화
- Job 상태 관리

---

# Communication Flow

자세한 API 명세는 [API_SPECIFICATION.md](./docs/API_SPECIFICATION.md) 참조

---

# Worker Internal Architecture

## Components

### API Layer

기술:
- FastAPI

역할:
- Request validation
- Job creation
- Job status API

---

## Queue Layer

기술:
- Redis
- Celery

역할:
- 비동기 Job 처리
- Retry
- Timeout 관리

---

## MCP Server (Playwright + Claude Integration)

**기술:**
- Model Context Protocol (MCP)
- Anthropic Claude API
- Playwright (MCP 도구로 제공)

**역할:**

MCP는 Claude가 직접 웹사이트에 접근하고 분석하는 표준 프로토콜이다.

```
Worker → MCP Server (Playwright)
         ↓
Claude API (with MCP tools)
         ↓
Claude가 자동으로:
  1. Playwright로 웹사이트 렌더링
  2. Screenshot 생성
  3. 콘텐츠 추출
  4. AI 사이트 판별
  5. 카테고리 분류
  6. 점수 계산
  7. 요약 생성
```

**구현 (토큰 최적화):**

```python
from anthropic import Anthropic
from mcp_playwright import PlaywrightServer
import json

# 1. MCP 서버 시작 (Worker 시작 시)
async def start_mcp_server():
    server = PlaywrightServer()
    await server.start()

# 0. 캐싱 전용 시스템 프롬프트 정의 (모든 호출에서 재사용)
SYSTEM_PROMPT = """You are an AI service analyzer. Analyze websites and classify them.

Category levels:
- level_1: text|image|video|audio|code|multimodal|data|business
- level_2: text-generation|text-analysis|conversational|image-generation|image-editing|video-generation|speech-generation|code-generation|etc
- level_3: (optional) blog-writing|copywriting|realistic-image|voice-cloning|etc
- tags: (optional) ["multilingual","api-available","free-tier","webhook"]

Respond in JSON format only, no markdown."""

# 2. Claude가 MCP를 통해 분석 수행 (토큰 최적화)
async def analyze_with_mcp(url: str) -> dict:
    """Claude가 직접 웹사이트를 분석 (Prompt Caching 활용)"""
    
    client = Anthropic()
    
    # 시스템 프롬프트 (캐싱 가능 - 모든 요청에서 동일)
    system_prompt = """You are an AI service analyzer. Analyze websites and classify them.

Category levels:
- level_1: text|image|video|audio|code|multimodal|data|business
- level_2: text-generation|text-analysis|conversational|image-generation|image-editing|video-generation|speech-generation|code-generation|etc
- level_3: (optional) blog-writing|copywriting|realistic-image|voice-cloning|etc
- tags: (optional) ["multilingual","api-available","free-tier","webhook"]

Respond in JSON format only, no markdown."""
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}  # ← 프롬프트 캐싱 (90% 토큰 절감)
            }
        ],
        tools=[
            {
                "type": "mcp",
                "name": "playwright"
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Analyze {url}: is_ai_tool, category (level_1, level_2, level_3, tags), scores (utility/trust/originality 1-10), summary (한국어)"
            }
        ]
    )
    
    # Claude가 MCP로 렌더링하고 분석한 결과 파싱
    return parse_claude_response(response)
```

**장점:**

- ✅ 구현 간단 (Content Extractor, Scoring Engine 불필요)
- ✅ Claude가 지능적으로 콘텐츠 선택
- ✅ 에러 처리 자동 (렌더링 실패, 파싱 오류 등)
- ✅ 유지보수 최소화 (Claude 개선이 자동 반영)
- ✅ Worker 메모리 효율 (로컬 브라우저 풀 불필요)

---

## Processing Pipeline (MCP 방식 + 토큰 최적화)

```
Queue
  ↓
Celery Task: analyze_with_cache(url)
  ├─ 1. DB에서 기존 분석 확인 (캐시)
  │  ├─ 있음 → 결과 반환 (API 호출 안 함)
  │  └─ 없음 → 2번 진행
  ├─ 2. Claude API 호출 (with Playwright MCP + Prompt Caching)
  │  ├─ Claude가 MCP 도구로 Playwright 사용
  │  │  ├─ 웹사이트 렌더링
  │  │  ├─ Screenshot 생성
  │  │  └─ 콘텐츠 추출
  │  ├─ Claude가 콘텐츠 분석
  │  │  ├─ AI 서비스 여부 판별
  │  │  ├─ 카테고리 분류
  │  │  ├─ 점수 계산 (utility, trust, originality)
  │  │  └─ 한 문장 요약 생성
  │  └─ (Prompt 캐시 히트: 90% 토큰 절감)
  ├─ 3. Pydantic으로 결과 검증 및 정규화
  ├─ 4. PostgreSQL DB에 저장
  └─ 5. Job 상태 업데이트 (completed)
```

**토큰 최적화 적용:**
- **Prompt Caching**: 시스템 프롬프트 캐싱 (90% 절감)
- **DB 캐싱**: 중복 분석 제거 (100% 절감)
- **프롬프트 단순화**: 불필요한 설명 제거 (30~40% 절감)

**핵심:**
- **MCP Server**: Worker 내부에서 실행되며, Claude에게 Playwright 도구 제공
- **Claude API**: 분석 요청, MCP를 통해 필요시 Playwright 접근 (Prompt Caching 활용)
- **Playwright**: MCP 도구로서 Claude가 사용 (Worker가 직접 관리 안 함)
- **DB Cache**: 새로운 URL만 Claude로 분석, 기존 URL은 DB에서 조회

---

# Recommended Tech Stack

| Layer | Technology | 설명 |
|---|---|---|
| API | FastAPI | 비동기 API 서버 |
| Queue | Celery | 비동기 작업 큐 |
| Broker | Redis | 작업 큐 브로커 |
| MCP Server | Playwright MCP | 웹 렌더링 (Claude와 통합) |
| LLM | Anthropic Claude | AI 사이트 분석 (MCP 지원) |
| Validation | Pydantic | 결과 검증 및 정규화 |
| Database | PostgreSQL | 결과 저장 |
| ORM | SQLAlchemy | 데이터베이스 접근 |
| Container | Docker | 배포 |

---

## Architecture Diagram (MCP 방식)

```
┌──────────────────────────────────────────────────────────────┐
│                    Spring Backend                             │
│                  (사용자 요청 처리)                            │
└────────────────────┬─────────────────────────────────────────┘
                     │ POST /analyze?url=...
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                   FastAPI Worker                              │
│         ┌─────────────────────────────────────┐              │
│         │  API Layer                          │              │
│         │  - Request validation               │              │
│         │  - Job creation                     │              │
│         └─────────────────────────────────────┘              │
└────────────────────┬─────────────────────────────────────────┘
                     │ enqueue
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                  Redis Queue (Celery)                         │
│            (비동기 작업 큐 및 상태 저장소)                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│              Celery Worker Process                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        MCP Server (Playwright)                       │   │
│  │  - 브라우저 자동화                                   │   │
│  │  - Screenshot 생성                                   │   │
│  │  - DOM 접근 (Claude가 사용)                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   Claude API (with MCP tools)                        │   │
│  │  - AI 사이트 판별                                    │   │
│  │  - 카테고리 분류                                     │   │
│  │  - 점수 계산                                         │   │
│  │  - 요약 생성                                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   Result Normalizer (Pydantic)                       │   │
│  │  - JSON 검증                                         │   │
│  │  - Schema 정규화                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬─────────────────────────────────────────┘
                     │ 결과 저장
                     ▼
┌──────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                              │
│  - AnalysisJob (작업 추적)                                   │
│  - AISite (분석 결과)                                        │
│  - UserBookmark (사용자 폴더)                                │
└──────────────────────────────────────────────────────────────┘
```

---

# Directory Structure (MCP 방식)

```text
sw-test/
├── src/
│   ├── __init__.py
│   ├── main.py                 # 애플리케이션 진입점 (FastAPI + Celery)
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # 환경 변수 및 설정 (DB, Redis, API 키)
│   │   └── database.py         # SQLAlchemy 엔진 및 세션 관리
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # FastAPI 라우트 (POST /analyze, GET /jobs/{id})
│   │   └── dependencies.py     # FastAPI 의존성 (DB 세션, 인증)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ai_site.py          # AISite ORM 모델
│   │   ├── analysis_job.py     # AnalysisJob ORM 모델
│   │   └── user_bookmark.py    # UserBookmark ORM 모델
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── analysis.py         # Pydantic 스키마 (분석 결과 정규화)
│   │   ├── job.py              # Job 요청/응답 스키마
│   │   └── site.py             # AISite 요청/응답 스키마
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py       # Celery 앱 초기화
│   │   ├── analyze_task.py     # 분석 태스크 (Claude API + MCP)
│   │   └── tasks.py            # 기타 태스크 (캐시 무효화 등)
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── client.py           # Claude API 클라이언트 (MCP 도구 사용)
│   │   └── prompts.py          # Claude 프롬프트 (시스템 메시지)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analysis_service.py # 분석 로직 (Claude 호출)
│   │   └── validation_service.py # 결과 검증 (Pydantic)
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── logging.py          # 로깅 설정
│   │   └── metrics.py          # 성능 메트릭 수집
│   └── utils/
│       ├── __init__.py
│       ├── errors.py           # 커스텀 예외 클래스
│       └── helpers.py          # 유틸리티 함수
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest 설정 및 fixture
│   ├── unit/
│   │   ├── test_analysis.py    # 분석 로직 단위 테스트
│   │   ├── test_validation.py  # 검증 로직 단위 테스트
│   │   └── test_models.py      # ORM 모델 테스트
│   ├── integration/
│   │   ├── test_api.py         # API 엔드포인트 통합 테스트
│   │   └── test_workers.py     # Celery 태스크 통합 테스트
│   └── e2e/
│       └── test_analysis_flow.py # 전체 분석 플로우 E2E 테스트
├── docs/
│   ├── API_SPECIFICATION.md    # API 명세
│   ├── DATA_MODEL.md           # 데이터베이스 스키마
│   ├── PLANS.md                # Phase별 구현 계획
│   └── CATEGORY_TAXONOMY.md    # 카테고리 분류 체계
├── migrations/
│   ├── versions/               # Alembic 마이그레이션 파일
│   └── env.py                  # Alembic 환경 설정
├── .env.example                # 환경 변수 예시
├── .gitignore                  # Git 무시 파일
├── ARCHITECTURE.md             # 아키텍처 설명서 (현재 파일)
├── CLAUDE.md                   # Claude Code 지시사항
├── requirements.txt            # Python 의존성
├── pyproject.toml              # 프로젝트 설정 (선택사항)
├── docker-compose.yml          # Docker 개발 환경
├── Dockerfile                  # 컨테이너 빌드 설정
└── README.md                   # 프로젝트 개요 및 시작 가이드
```

---

## 주요 디렉토리 설명

### `src/`
프로덕션 코드 모음

- **api/**: FastAPI 라우트 및 엔드포인트
- **models/**: SQLAlchemy ORM 모델 (데이터베이스 테이블 매핑)
- **schemas/**: Pydantic 스키마 (요청/응답 검증 및 직렬화)
- **workers/**: Celery 태스크 (비동기 작업)
- **mcp/**: Claude API 클라이언트 (MCP 도구 사용)
- **services/**: 비즈니스 로직 (분석, 검증)
- **config/**: 환경 설정 및 데이터베이스 연결
- **observability/**: 로깅 및 메트릭 수집
- **utils/**: 공통 유틸리티 및 헬퍼 함수

### `tests/`
자동화된 테스트

- **unit/**: 개별 컴포넌트 단위 테스트
- **integration/**: 여러 컴포넌트 간 상호작용 테스트
- **e2e/**: 전체 시스템 엔드-투-엔드 테스트

### `docs/`
문서화

- API 명세서
- 데이터 모델 정의
- 구현 계획
- 분류 체계

### `migrations/`
데이터베이스 마이그레이션 스크립트 (Alembic)

---

**단순화된 구조:**
- Content Extractor 불필요 (Claude가 처리)
- Scoring Engine 불필요 (Claude가 계산)
- Classifier, Evaluator, Summarizer 모두 불필요 (Claude가 통합 처리)
- Playwright 직접 관리 불필요 (MCP 서버가 제공)

---

# Data Model

자세한 데이터베이스 스키마는 [DATA_MODEL.md](./docs/DATA_MODEL.md) 참조

---

---

**자세한 내용은 [Token Optimization Strategy](./TOKEN_OPTIMIZATION.md) 참고**

---

# Timeout Strategy (MCP 방식)

| Step | Timeout | 담당자 |
|---|---|---|
| Playwright 렌더링 | 30s | Claude (MCP 도구) |
| Claude 분석 요청 | 60s | Claude API |
| 결과 정규화 | 10s | Pydantic |
| **전체 Celery Task** | **120s** | Celery |

**참고:**
- Claude API 호출은 Worker 입장에서 외부 요청이므로 timeout 필요
- MCP 도구 호출 (렌더링)은 Claude가 내부 처리하므로 Claude timeout에 포함

---

# Failure Handling

실패도 정상 상태로 처리한다.

예시:

```json
{
  "job_id": "uuid",
  "status": "failed",
  "reason": "timeout"
}
```

가능한 실패 유형:

- timeout
- navigation error
- anti-bot detection
- invalid domain
- LLM failure

---

# Design Principles

## 1. Worker is Stateless

Worker는 상태를 내부 메모리에 저장하지 않는다.

모든 상태는:
- Redis (작업 큐, Job 상태)
- PostgreSQL DB (분석 결과)

를 통해 관리한다.

---

## 2. Queue First Architecture

모든 분석 작업은 Celery Queue를 통해 수행한다.

동기 처리 금지.

```
API (즉시 Job ID 반환)
  ↓
Celery Queue (비동기 처리)
  ↓
DB (결과 저장)
```

---

## 3. MCP-First Analysis

LLM 분석은 MCP를 통해 수행한다.

Claude가 MCP 도구로 Playwright 접근:
- 렌더링 (Claude가 수행)
- 콘텐츠 추출 (Claude가 수행)
- 판별 및 분류 (Claude가 수행)

Worker는 결과 정규화만 수행.

---

## 4. Structured Output Validation

Claude 응답을 Pydantic으로 검증한다.

반드시:
- JSON schema 검증
- 타입 검증
- 필드 완성도 확인

를 수행한다.

---

# Future Expansion

향후 확장 가능 기능:

- Multi-page crawling
- AI site ranking
- Embedding search
- Similar service detection
- Anti-bot bypass
- Browser pool optimization
- Screenshot OCR
- Multi-modal analysis
- Product Hunt integration

---

# MVP Scope

초기 MVP 목표:

입력:
- URL 1개

출력:
- AI 사이트 여부
- 카테고리
- usefulness score
- summary
- screenshot

복잡한 랭킹/추천 시스템은 MVP 범위에서 제외한다.

---

# Result Storage Strategy

## 요구사항

- 사용자가 AI 사이트를 **폴더 구조로 북마크** 관리
- 분석 결과 **영구 저장** (데이터 손실 금지)
- 검색/필터링 가능
- 카테고리별 조직화

## 선택: Worker Direct DB Save

Worker가 분석 결과를 **DB에 직접 저장**하는 방식을 채택한다.

**이유:**
- 가장 간단한 구현
- 데이터 일관성 보장 (DB 단일 출처)
- 사용자 북마크 지원
- Transaction 지원

**흐름 (MCP 방식):**
```
API: POST /analyze?url=...
    ↓
FastAPI 엔드포인트 (Request validation)
    ↓
Job ID 생성 & DB 저장 (status: "queued")
    ↓
Celery Task enqueue
    ↓
Celery Worker Processing (비동기)
    ├─ Claude API 호출 (with MCP)
    │  ├─ Playwright로 렌더링 (MCP tool)
    │  ├─ 콘텐츠 추출
    │  ├─ AI 판별 + 분류
    │  ├─ 점수 계산
    │  └─ 요약 생성
    ├─ Pydantic 정규화
    └─ 결과 검증
    ↓
결과 DB에 직접 저장 (AISite table)
    ↓
Job 상태 업데이트 (status: "completed")
    ↓
사용자: 폴더/북마크로 조직화
```

**MCP의 이점:**
- Worker 코드 간단 (Claude API 호출만)
- 렌더링 & 분석 통합 (Claude가 지능적으로 수행)
- 에러 처리 자동
- 유지보수 최소

---



## Performance Optimization Roadmap

4단계 최적화 계획입니다.

**자세한 내용은 [Performance Roadmap](./PERFORMANCE_ROADMAP.md) 참고**

### 요약

| 단점 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|--------|--------|--------|---------|
| **응답 느림** | - | ✅ (10배↑) | ✅ (즉시) | ✅ (즉시) |
| **DB 병목** | ✅ (인덱스) | ✅ (캐시) | ✅ (쓰기 분산) | ✅ (읽기 분산) |
| **쓰기 느림** | - | - | ✅ (5~10배↑) | ✅ (5~10배↑) |
| **구현 난도** | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **비용** | 낮음 | 낮음 | 중간 | 높음 |

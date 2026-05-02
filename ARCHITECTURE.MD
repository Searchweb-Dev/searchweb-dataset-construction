# ARCHITECTURE.md

# AI Website Evaluation Worker Architecture

## Overview

이 프로젝트는 URL을 입력받아 웹사이트를 분석하고,
해당 사이트가 유용한 AI 서비스인지 평가하는 독립형 Worker 시스템이다.

Worker는 Spring Backend와 분리된 서비스로 동작하며,
다음 기능을 담당한다:

- Playwright 기반 웹 렌더링
- 웹사이트 콘텐츠 추출
- Screenshot 생성
- LLM 기반 AI 사이트 분석
- 구조화된 결과 생성
- 비동기 Job 처리

---

# High Level Architecture

```text
+----------------------+
| Spring Backend       |
|----------------------|
| API / Auth / DB      |
+----------+-----------+
           |
           | HTTP Request
           v
+----------------------+
| Python Worker API    |
|----------------------|
| FastAPI              |
+----------+-----------+
           |
           | enqueue
           v
+----------------------+
| Redis Queue          |
+----------+-----------+
           |
           v
+----------------------+
| Worker Processor     |
|----------------------|
| Playwright           |
| Content Extractor    |
| LLM Analyzer         |
| Scoring Engine       |
+----------+-----------+
           |
           v
+----------------------+
| Result Storage       |
+----------------------+
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

## 1. Analyze Request

Spring Backend가 Worker에 분석 요청을 보낸다.

### Request

```http
POST /analyze
Content-Type: application/json
```

```json
{
  "url": "https://example.com"
}
```

---

## 2. Immediate Response

Worker는 즉시 Job ID를 반환한다.

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

Worker는 절대 동기적으로 분석 결과를 반환하지 않는다.

---

## 3. Background Processing

Worker 내부 Queue에서 비동기 분석을 수행한다.

Processing Pipeline:

```text
Queue
  -> Crawl
  -> Extract
  -> Screenshot
  -> Analyze
  -> Score
  -> Normalize
  -> Store Result
```

---

## 4. Result Polling

Spring Backend는 polling 방식으로 상태를 조회한다.

### Request

```http
GET /jobs/{job_id}
```

### Processing Response

```json
{
  "job_id": "uuid",
  "status": "processing"
}
```

### Completed Response

```json
{
  "job_id": "uuid",
  "status": "completed",
  "result": {
    "url": "https://example.com",
    "is_ai_tool": true,
    "category": "image-generation",
    "scores": {
      "utility": 8.4,
      "trust": 7.9,
      "originality": 6.8
    },
    "summary": "AI 기반 이미지 생성 플랫폼",
    "screenshot_url": "https://..."
  }
}
```

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

## Playwright Crawler

역할:
- 브라우저 렌더링
- JavaScript 실행
- DOM 로딩 대기
- Screenshot 생성
- 텍스트 추출

---

## Content Extractor

LLM에 전달할 핵심 콘텐츠만 추출한다.

추출 대상:

- title
- meta description
- headings
- CTA buttons
- pricing text
- feature descriptions
- footer/company information

HTML 전체는 LLM에 전달하지 않는다.

---

## LLM Analyzer

역할:

- AI 서비스 여부 판별
- 카테고리 분류
- 유용성 평가
- 신뢰도 평가
- 요약 생성

---

## Scoring Engine

LLM 결과를 기반으로 구조화된 점수를 생성한다.

예시 항목:

- Utility
- Trust
- Originality
- Accessibility
- UX

---

## Result Normalizer

LLM 출력 결과를 schema 기반으로 검증 및 정규화한다.

기술:
- Pydantic

---

# Recommended Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Queue | Celery |
| Broker | Redis |
| Browser Automation | Playwright |
| Validation | Pydantic |
| HTTP Client | httpx |
| Retry | tenacity |
| LLM SDK | OpenAI / Anthropic |
| Container | Docker |

---

# Directory Structure

```text
/worker
  /api
    routes.py

  /crawler
    playwright_client.py
    extractor.py

  /analyzer
    classifier.py
    evaluator.py
    summarizer.py

  /scoring
    scoring_engine.py

  /schemas
    result.py
    job.py

  /prompts
    classifier.txt
    evaluator.txt
    summarizer.txt

  /storage
    screenshot.py

  /tasks
    analyze_task.py

  main.py
```

---

# Data Model

## Job Status

```text
queued
processing
completed
failed
timeout
```

---

## Analysis Result Schema

```json
{
  "url": "string",
  "is_ai_tool": true,
  "category": "string",
  "scores": {
    "utility": 0,
    "trust": 0,
    "originality": 0
  },
  "summary": "string",
  "screenshot_url": "string"
}
```

---

# Timeout Strategy

| Step | Timeout |
|---|---|
| page.goto | 30s |
| extraction | 10s |
| LLM request | 60s |
| total job | 120s |

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
- Redis
- DB
- Object Storage

를 통해 관리한다.

---

## 2. Queue First Architecture

모든 분석 작업은 Queue를 통해 수행한다.

동기 처리 금지.

---

## 3. Structured Output First

LLM raw output을 직접 사용하지 않는다.

반드시:
- validation
- normalization
- schema enforcement

를 수행한다.

---

## 4. Browser Automation Isolation

Playwright는 독립 계층으로 분리한다.

Crawler 로직과 LLM 로직을 직접 결합하지 않는다.

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

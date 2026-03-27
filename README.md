# AI Tool/Service Dataset 구축 문서 (v1.1.0)

## 테스트 방법 (Bash 기준)

현재 코드는 로컬 CLI 기반 평가 파이프라인까지만 구현되어 있다.
아직 Postgres 등 외부 DB에 대한 세션 연결, 저장, 조회 연동은 포함되어 있지 않다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # uv 설치
uv venv --python 3.13                             # .venv 가상환경 생성 (파이썬 버전 3.13)
source .venv/bin/activate                         # Bash에서 가상환경 활성화
uv pip install -r requirements.txt                # 프로젝트 의존성 설치
playwright install chromium                       # Chromium 브라우저 설치
```

```bash
python src/main.py https://chatgpt.com                      # 한 개의 사이트 평가 실행
python src/main.py https://chatgpt.com https://claude.com   # 여러 사이트를 한 번에 평가 실행
```

여러 URL은 공백으로 나열해 한 번에 실행할 수 있다.

쿼리스트링이 포함된 URL은 반드시 따옴표(`"` 또는 `'`)로 감싸서 실행한다.
셸에서 `&`가 백그라운드 실행 기호로 해석되어 URL이 잘릴 수 있다.

```bash
# 쿼리스트링이 있는 URL 실행 예시
python src/main.py "https://news.google.com/home?hl=ko&gl=KR&ceid=KR%3Ako"  
```

## 1. 프로젝트 개요

### 목적
- SearchWeb 서비스에서 활용할 신뢰도 높은 AI Tool/Service Reference Database를 구축한다.
- 단순 툴 나열이 아니라, 검증된 고품질 도구를 구조화해 검색/필터/비교/추천에 바로 사용 가능한 데이터셋을 만든다.

### 배경
- AI 서비스가 빠르게 증가하면서 사용자가 도구를 신뢰성 있게 선택하기 어려워졌다.
- 초기에는 엄격한 수동 큐레이션으로 품질 기준을 고정하고, 이후 자동 파이프라인으로 확장한다.

### 확장 방향
- 1차: `200개 이하`의 고품질 curated 데이터셋 구축.
- 2차: JTBD/요구조건 기반 추천(RAG 포함)으로 확장.

---

## 2. 아키텍처 원칙

### 기본 원칙
- 서비스 DB와 수집/정제/검증 파이프라인을 분리한다.
- 서비스는 검증 완료 데이터(`curated`, 필요 시 `incubating`)만 읽기 중심으로 사용한다.
- 현재 저장소에는 DB 세션 생성, 커넥션 관리, ORM/쿼리 레이어가 아직 구현되어 있지 않다.

### 논리 구조
```text
[External Data Pipeline]
        ↓
(정제/분류/검증 완료 데이터)
        ↓
[DB Load / Upsert Layer]
        ↓
[Postgres - Service DB]
        ↓
[SearchWeb Serving]
```

### 분리 이유
- 크롤링/LLM 실패나 지연이 서비스 응답에 영향을 주지 않게 하기 위함.
- LLM 비용/재시도/스케줄링을 독립적으로 운영하기 위함.
- 안정성, 추적성, 확장성을 확보하기 위함.

---

## 3. 현재 코드 모듈 구조 (반영 완료)

실행 엔트리포인트는 `src/main.py` 하나이며, 내부 기능은 모듈별로 분리되어 있다.

- `src/main.py`
  - 단일 실행 파일(CLI)
  - URL 목록을 받아 파이프라인 실행
  - 파이프라인 단계 정의(fetch → extract → ai_scope → classify → criteria → score/status → review → summary)
  - 현재 구현은 평가 결과 생성까지 담당하며, DB 적재 단계는 아직 포함하지 않음
  - `PageFetcher`를 생성하고 `WeightedQualityEvaluator`에 주입
  - URL 병렬 평가 및 후보 URL 병렬 수집 실행
  - `DEFAULT_PIPELINE_STEPS` 포함
- `src/config.py`
  - 파이프라인/평가/수집 관련 전역 설정(`EvalConfig`)
  - `max_sub_tasks`, 병렬 옵션, Playwright 옵션 포함
- `src/models.py`
  - 결과 데이터 구조(`FetchResult`, `CriterionResult`, `EvaluationResult` 등)
- `src/page_fetcher.py`
  - requests + playwright 기반 페이지 수집
  - lightweight candidate fetch, 링크/본문 길이 상한 적용
- `src/discovery_signals.py`
  - 후보 URL 수집/구조화 신호(extracted) 추출
- `src/ai_scope_classifier.py`
  - 평가 대상이 AI 사이트인지 스코프 게이트 판정
- `src/taxonomy_classifier.py`
  - (AI 사이트로 판정된 경우에만) 규칙 기반 카테고리/태그 분류
  - sub-task는 `config.max_sub_tasks`까지 반환
- `src/criteria_evaluator.py`
  - 5개 criteria 평가
  - 공통 evaluator 베이스 및 최종 `EvaluationResult` 조립
  - `fetcher`를 생성하지 않고 외부(메인)에서 주입받아 사용
  - 가중치 점수 기반 상태 판정 evaluator(`WeightedQualityEvaluator`)
- `src/status_policy.py`
  - review gate 및 summary 정책
- `src/keywords.py`
  - 카테고리/서브태스크/플랫폼/정책 판정용 키워드 사전
- `src/utils.py`
  - URL 정규화, 텍스트 정리, 키워드 매칭, 링크 판정 유틸 함수

---

## 4. 데이터 범위

### 포함 대상
- 생성형 AI 기반 SaaS
- AI 기능 포함 자동화/워크플로우 툴
- API 제공 AI 서비스
- 실사용 가능한 오픈소스 AI 툴
- 진입장벽이 낮은 AI 서비스

### 제외 대상
- 뉴스/블로그/정보성 콘텐츠
- 기능 불명확 랜딩 페이지
- 접근 불가/종료 서비스

---

## 5. 분류 기준 (Taxonomy)

### 5.1 Top-level Category (Primary 1개 필수)
- Writing & Docs
- Coding
- Research
- Design & Creative
- Data & Analytics
- Ops & Automation
- Meeting & Sales
- DevOps / Security

### 5.2 Sub-task (다중 태그)

#### Writing & Docs
- 이메일 작성, 보고서 작성, PRD 작성, 제안서 작성
- 블로그/콘텐츠 작성, 요약, 번역, 교정, 재작성, 문체 변환

#### Coding
- IDE 에이전트, 코드 생성, 코드 리뷰, 테스트 코드 생성
- 리팩토링, 버그 분석, 코드 설명, API 스펙/주석 생성

#### Research
- 웹 리서치, 경쟁사 분석, 논문 분석, 시장 조사
- 리포트 분석, 트렌드 분석, 문서 QA, 데이터 수집 요약

#### Design & Creative
- 이미지/영상 생성 및 편집
- 프레젠테이션 제작, 브랜딩/로고, UI 컨셉, 목업 생성

#### Data & Analytics
- SQL 생성/튜닝, 데이터 정제, 대시보드/시각화
- A/B 테스트 분석, 통계 분석, 리포트 자동 생성

#### Ops & Automation
- 워크플로우 자동화, API 연동, 티켓 자동 분류
- CS 응답 자동화, 알림 자동화, 문서 자동 처리, 스케줄링

#### Meeting & Sales
- 회의 요약/녹취 분석, 액션 아이템 추출
- CRM 입력 자동화, 세일즈 이메일/스크립트/제안서 자동화

#### DevOps / Security
- 로그 분석, 장애 원인 분석, 취약점 분석
- 정책 생성, 컴플라이언스 점검, PII 마스킹, 권한 분석

> 구현 메모: 현재 코드는 `max_sub_tasks` 설정값(`src/config.py`)으로 반환 개수를 제한한다.

### 5.3 Meta Category (옵션)
- Create
- Analyze
- Build
- Automate
- Communicate
- Secure

---

## 6. 품질 평가 지표

### 공통 5개 지표 (criteria)
- `usable_now`: 실제 즉시 사용 가능 여부
- `clear_function_desc`: 기능 설명 명확성
- `has_pricing`: 요금/플랜 공개 여부
- `has_docs_or_help`: 문서/도움말 존재 여부
- `has_privacy_or_data_policy`: 정책 페이지 존재 여부

### Weighted 기준
- 가중치와 총점(0~100)을 함께 사용
- 하한 게이트(usable/desc/docs/policy 최소치) + 상태 컷(`curated`, `incubating`) 적용
- 기본 가중치(현재 코드):
  - `usable_now=0.30`
  - `clear_function_desc=0.25`
  - `has_docs_or_help=0.20`
  - `has_privacy_or_data_policy=0.20`
  - `has_pricing=0.05`

---

## 7. 상태 모델

- 현재 코드의 `predicted_status` / `final_status`는 아래 3가지만 사용:
  - `curated`
  - `incubating`
  - `rejected`
- `review gate`에서 `curated`가 `incubating`으로 다운그레이드될 수 있다.
- `discovered`, `validated`, `deprecated`는 데이터 운영 레이어에서 확장 가능한 개념 상태로 유지한다.

---

## 8. 데이터 파이프라인 (현재 구현 단계)

`src/main.py`의 `DEFAULT_PIPELINE_STEPS` 기준 실행 순서:

1. 홈페이지 및 후보 페이지 수집 (`step_fetch_and_collect_pages`)
2. 구조화 신호 추출 (`step_extract_signals`)
3. AI 사이트 스코프 게이트 판정 (`step_assess_ai_scope`)
4. 분류 체계(Taxonomy) 판정 (`step_classify_taxonomy`)
5. 5개 품질 기준 평가 (`step_evaluate_criteria`)
6. 점수 계산 및 1차 상태 예측 (`step_score_and_predict_status`)
7. 검수 게이트 반영 및 최종 상태 확정 (`step_review_and_finalize_status`)
8. 결과 요약문 생성 (`step_build_summary`)

운영 확장(중복 제거/DB 반영/변경로그/주기 재검증)은 별도 데이터 파이프라인 레이어에서 연결한다.
현재 저장소 범위에는 DB 적재 파이프라인과 세션 연결 코드가 포함되지 않는다.

### 목표 파이프라인의 최종 단계

이 문서는 데이터셋 구축 파이프라인을 설명하므로, 운영 기준의 최종 단계에는 DB 적재가 포함되어야 한다.

1. 홈페이지 및 후보 페이지 수집
2. 구조화 신호 추출
3. AI 사이트 스코프 게이트 판정
4. 분류 체계(Taxonomy) 판정
5. 5개 품질 기준 평가
6. 점수 계산 및 상태 예측
7. 검수 게이트 반영
8. 결과 요약 및 적재용 레코드 정규화
9. Service DB(Postgres) 적재 또는 upsert
10. 변경 이력(Change Log) 기록 및 후속 재검증 대상 등록

### DB 적재 단계에서 해야 할 일

- 평가 결과를 서비스 스키마에 맞는 레코드로 정규화
- 기준 URL 또는 canonical URL 기준으로 중복 여부 판정
- 신규 데이터는 insert, 기존 데이터는 upsert
- 상태, 점수, 가격/정책 변경 여부를 비교해 변경 이력 기록
- 적재 성공/실패 결과와 재시도 대상을 분리 관리

현재 저장소에는 위 단계를 수행하는 DB 세션 연결, insert/upsert, 변경 이력 기록 로직이 아직 구현되어 있지 않다.

---

## 9. LLM 구조화 단계

현재 코드 기준:
- taxonomy 분류(`primary_category`, `sub_tasks`, `meta_categories`, `platforms` 등)는 **규칙 기반**이다.
- LLM은 `clear_function_desc` 기준에서만 선택적으로 사용 가능하다(`enable_llm_for_clear_desc=True`).
- 기본 실행(`src/main.py`)은 `use_llm=False`로 동작한다.

운영 방식(자동 반영/검수 비율/배치 주기)은 데이터 엔지니어링 정책으로 관리한다.

---

## 10. DB 설계 요구사항 (Postgres)

### 필수 요구
- 카테고리 기반 필터링
- 점수 기반 정렬
- 상태 기반 조회
- 정책/가격 변경 추적
- Change Log 유지

### 적재 관점 요구
- 사이트의 canonical 식별자 기준 upsert 가능해야 함
- 평가 시점(`evaluated_at`)과 적재 시점(`ingested_at`)을 분리해 저장해야 함
- 현재 스냅샷 테이블과 변경 이력 테이블을 분리해 관리해야 함
- 재검증 주기 대상과 적재 실패 대상을 추적할 수 있어야 함

### 설계 선택지
- 정규화 중심 vs JSONB 중심은 성능/운영 전략에 따라 결정

---

## 11. 운영 전략

### 정기 검증
- 분기별 재검토
- 가격 변경 감지
- 정책 변경 감지
- 서비스 종료 감지

### Change Log 필수
- 점수 변경
- 정책 변경
- 카테고리 변경
- 상태 변경

---

## 12. MVP 목표

- 200개 이하 curated AI Tool
- 전부 검증 통과
- 구조화 완료
- 검색/필터/정렬 가능

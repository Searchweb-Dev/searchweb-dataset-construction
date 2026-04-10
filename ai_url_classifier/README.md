# AI URL Classifier (v1.1.2)

AI 툴/서비스 후보 URL을 입력으로 받아, 공개 웹페이지에서 확인 가능한 신호만으로 해당 사이트가 실제 AI 서비스인지 판정하고, taxonomy와 품질 상태를 평가해 JSON으로 출력하는 로컬 CLI 파이프라인이다.

현재 구현 범위:

- URL 입력 수집
- `requests` + `Playwright` 기반 페이지 fetch
- 후보 pricing/docs/policy/product 페이지 탐색
- AI 사이트 스코프 게이트 판정
- taxonomy 분류
- 5개 품질 기준 평가
- weighted score 계산
- review gate 반영
- 최종 JSON 출력

현재 구현 범위 밖:

- Postgres 적재
- ORM/세션 연결
- insert/upsert
- change log 저장
- 자동 스케줄링
- 실제 외부 LLM 연동
- 자동화 테스트 코드

상세 코드 분석 문서:

- [research.md](/mnt/c/Users/kang/Desktop/sw_test/ai_url_classifier/research.md)

## 1. 빠른 실행

### 1.1 환경 준비

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt
playwright install chromium
```

의존성:

- `requests`
- `beautifulsoup4`
- `playwright`

### 1.2 실행 예시

```bash
python run.py https://chatgpt.com
python run.py https://chatgpt.com https://claude.com
python run.py "https://news.google.com/home?hl=ko&gl=KR&ceid=KR%3Ako"
python run.py data/site_url_list.txt
python run.py --url-file data/site_url_list.txt
```

입력 규칙:

- 여러 URL을 공백으로 나열해 한 번에 실행할 수 있다.
- `.txt` 파일 경로를 직접 넘기면 줄 단위 URL 목록으로 읽는다.
- `--url-file <path>`도 지원한다.
- 쿼리스트링이 포함된 URL은 반드시 따옴표로 감싸야 한다.
- 셸에서 `&`는 백그라운드 실행 기호로 해석되므로 URL이 잘릴 수 있다.

## 2. 출력 형태

출력은 표준 출력(stdout)으로 JSON 배열 하나를 내보낸다.

각 항목에는 아래 정보가 포함된다.

- 입력 URL과 정규화 URL
- `predicted_status`, `final_status`
- `passed_count`, `hard_pass`
- `review_required`, `review_reasons`
- 5개 criterion 상세
- `summary`
- `extracted`
- `total_score`, `score_breakdown`

즉, 이 프로젝트는 단순 pass/fail 스크립트가 아니라, 근거와 중간 신호를 포함한 분석 결과 JSON 생성기다.

## 3. 현재 코드가 실제로 하는 일

파이프라인 기본 순서는 아래와 같다.

1. 홈페이지와 후보 페이지 수집
2. 구조화 신호 추출
3. AI 사이트 스코프 판정
4. taxonomy 분류
5. 5개 품질 기준 평가
6. weighted score 계산과 1차 상태 예측
7. review gate 반영과 최종 상태 확정
8. 결과 summary 생성

핵심 특징:

- 먼저 `AI 사이트인지`를 판정한 뒤 나머지 평가를 수행한다.
- `non_ai`로 판정되면 taxonomy 상세 분류와 품질 평가는 사실상 제외 모드로 들어간다.
- `curated`는 단순 고득점이 아니라 review-free 상태여야 최종 확정된다.

## 4. 상태 모델

현재 최종 상태는 아래 3개만 사용한다.

- `curated`
- `incubating`
- `rejected`

별도 스코프 판정 신호:

- `ai`
- `uncertain`
- `non_ai`

중요한 점:

- `scope_decision`은 상태값이 아니라 평가 흐름 제어용 신호다.
- `predicted_status`가 `curated`라도 review gate에 걸리면 `final_status`는 `incubating`으로 내려갈 수 있다.

## 5. 품질 평가 기준

현재 구현은 아래 5개 criterion을 평가한다.

- `usable_now`
- `clear_function_desc`
- `has_pricing`
- `has_docs_or_help`
- `has_privacy_or_data_policy`

### 5.1 `usable_now`

실제 사용/가입/설치/실행 경로가 공개돼 있는지 본다.

주요 신호:

- CTA 텍스트
- 동일 도메인 내 usable URL 힌트
- docs 페이지 내 install/quickstart/self-hosted 신호
- waitlist/coming soon/early access 같은 부정 신호

### 5.2 `clear_function_desc`

서비스가 “누구를 위해 무엇을 어떻게 하는지” 설명이 충분히 구체적인지 평가한다.

현재 기본 구현은 규칙 기반 문장 점수화다.

### 5.3 `has_pricing`

pricing/plans/billing 페이지 또는 OSS 라이선스 신호를 본다.

기본 정책:

- 공개 pricing 페이지가 있으면 통과
- `contact sales`만 있으면 기본적으로 실패
- OSS license는 제한적으로 pricing 근거로 인정

### 5.4 `has_docs_or_help`

docs/help/guide/faq 페이지 존재 여부를 본다.

기본 정책:

- FAQ only도 기본 설정에서는 docs로 인정

### 5.5 `has_privacy_or_data_policy`

privacy/data policy/terms/security 문서 존재 여부를 본다.

기본 정책:

- terms only도 기본 설정에서는 policy로 인정

## 6. weighted score 정책

현재 상태 예측은 단순 count 방식이 아니라 weighted score 방식이다.

기본 가중치:

- `usable_now = 0.30`
- `clear_function_desc = 0.25`
- `has_docs_or_help = 0.20`
- `has_privacy_or_data_policy = 0.20`
- `has_pricing = 0.05`

하한 게이트:

- `usable_now >= 0.60`
- `clear_function_desc >= 0.50`

상태 컷:

- `curated >= 85.0`
- `incubating >= 65.0`
- 그 외 `rejected`

추가 curated 조건:

- docs score 최소치 충족
- privacy/policy score 최소치 충족

즉, 가격 공개 여부는 비교적 낮은 비중이고, 실사용 가능성과 기능 설명 명확성이 더 중요하다.

## 7. AI 사이트 스코프 게이트

현재 구현은 AI 여부를 먼저 판정한다.

판정 방식:

- strong AI keywords
- weak AI keywords
- strong non-AI keywords
- weak non-AI keywords

점수식:

- `ai_signal_score = 2 * strong_ai + weak_ai`
- `non_ai_signal_score = 2 * strong_non_ai + weak_non_ai`
- `margin = ai_signal_score - non_ai_signal_score`

출력:

- `ai`
- `uncertain`
- `non_ai`

보조 신호:

- known AI brand domain
- `.ai` TLD

즉, 이 프로젝트는 taxonomy보다 먼저 “애초에 AI 툴/서비스 평가 대상인지”를 걸러낸다.

## 8. taxonomy 분류

AI 사이트로 간주된 경우에만 taxonomy를 상세 분류한다.

출력 범주:

- `primary_category`
- `sub_tasks`
- `meta_categories`
- `platforms`
- `pricing_model`
- `one_line_summary`

primary category 후보:

- Writing & Docs
- Coding
- Research
- Design & Creative
- Data & Analytics
- Ops & Automation
- Meeting & Sales
- DevOps / Security

sub-task는 선택된 primary category 안에서만 평가한다.

즉, primary category가 틀리면 sub-task도 연쇄적으로 왜곡될 수 있다.

## 9. 수집 전략

`PageFetcher`는 `requests`와 `Playwright`를 혼합 사용한다.

기본 원칙:

- 우선 `requests`
- 결과가 빈약하거나 challenge 페이지면 `Playwright`
- 특정 도메인은 Playwright 강제
- 둘 다 있으면 더 풍부한 결과를 선택

강제 Playwright 도메인:

- `chatgpt.com`
- `cursor.com`
- `perplexity.ai`

추가로 후보 페이지도 별도로 수집한다.

후보 종류:

- `pricing`
- `docs`
- `policy`
- `product`
- `probe`

fallback probe path:

- `/pricing`
- `/plans`
- `/docs`
- `/help`
- `/support`
- `/privacy`
- `/privacy-policy`
- `/terms`

## 10. anti-bot 대응

현재 fetcher는 Cloudflare/captcha/challenge 페이지를 감지한다.

대응 방식:

- Playwright 대기 및 재시도
- challenge 감지 시 `anti_bot_blocked` 신호 생성
- 정보 부족으로 완전 탈락하는 것을 막기 위해 일부 경우 `incubating` 완충 처리

즉, anti-bot으로 인해 본문 수집이 제한된 사이트를 무조건 `rejected`로 보내지 않는다.

## 11. 병렬 처리

병렬성은 두 층에 있다.

- URL 목록 병렬 평가
- 개별 URL 내부 후보 페이지 병렬 fetch

기본 설정:

- URL 평가 워커: `3`
- 후보 페이지 fetch 워커: `4`

중첩 병렬 시 후보 워커는 자동 축소될 수 있다.

이유:

- 과도한 스레드 증가 방지
- URL 병렬과 후보 병렬의 충돌 완화

## 12. LLM 사용 여부

현재 코드 기준:

- taxonomy는 규칙 기반이다.
- AI 스코프 판정도 규칙 기반이다.
- LLM은 `clear_function_desc`에만 선택적으로 연결 가능한 구조다.
- 기본 실행은 `use_llm=False`다.
- 현재 연결된 구현체는 실제 모델이 아니라 `DummyLLM` 스텁이다.

즉, 현재 저장소는 “LLM 연동이 가능한 자리”만 열어둔 상태고, 실제 외부 LLM API 호출은 구현되어 있지 않다.

## 13. 현재 한계

- 자동화 테스트 코드가 없다.
- DB 적재 코드가 없다.
- 출력은 stdout JSON뿐이다.
- query string이 URL 정규화 과정에서 제거된다.
- 키워드 사전 품질에 크게 의존한다.
- known-domain 예외 규칙이 일부 하드코딩돼 있다.

즉, 현재 구조는 실용적인 로컬 evaluator MVP이지만, 운영 품질을 높이려면 테스트와 룰 관리 체계가 다음 단계다.

## 14. 디렉터리 구조

```text
ai_url_classifier/
  README.md
  research.md
  requirements.txt
  run.py
  data/
    site_url_list.txt
  src/
    config.py
    keywords.py
    models.py
    pipeline.py
    utils.py
    fetchers/
      __init__.py
      page_fetcher.py
    classifiers/
      __init__.py
      ai_scope_classifier.py
      criteria_evaluator.py
      discovery_signals.py
      status_policy.py
      taxonomy_classifier.py
```

## 15. 향후 확장

현재 README는 실제 구현 범위를 기준으로 작성했다.  
향후 별도 단계에서 아래를 추가할 수 있다.

- Postgres 적재
- insert/upsert
- change log 저장
- 재검증 스케줄러
- 대표 사이트셋 기반 회귀 테스트
- 실제 LLM 연동

이 항목들은 현재 코드에 구현된 기능이 아니라, 다음 단계 설계 대상이다.

# ai_url_classifier 코드베이스 분석 보고서

## 1. 문서 목적

이 문서는 `ai_url_classifier/` 코드베이스를 정적으로 읽고, 현재 구현이 어떤 방식으로 동작하는지 상세하게 정리한 연구 보고서다.

분석 범위:

- 실행 엔트리포인트와 CLI 입력 처리
- URL 수집과 fetch 전략
- 구조화 신호 추출
- AI 사이트 판정 로직
- taxonomy 분류 로직
- 품질 criteria 평가 로직
- weighted score 및 status 결정
- review gate와 최종 상태 확정
- 병렬 처리 방식
- 설정값과 운영상 리스크

주의:

- 본 문서는 코드 정적 분석 기반이다.
- 외부 네트워크를 사용하는 실제 런타임 검증은 이번 분석 범위에 포함하지 않았다.

## 2. 코드베이스 개요

`ai_url_classifier`는 AI 툴/서비스 후보 URL을 입력으로 받아, 해당 URL이 실제로 AI 사이트인지 판별하고, 서비스 성격과 품질을 정량/정성 규칙으로 평가해 최종 상태를 산출하는 로컬 CLI 파이프라인이다.

핵심 특징:

- 단순 크롤러가 아니다.
- 수집 후 곧바로 분류/평가/상태 예측까지 수행한다.
- 출력은 DB 적재가 아니라 JSON 리스트다.
- 현재 구현은 규칙 기반(rule-based)이며, LLM은 기본적으로 비활성화돼 있다.

프로젝트 규모:

- 총 코드/문서 라인 수는 약 `3333`줄이다.
- 핵심 구현은 `src/` 아래에 집중되어 있다.
- `tests/` 디렉터리에 핵심 규칙(스코프/리뷰 게이트/known-domain seed) 단위 테스트가 추가되어 있다.

## 3. 파일 구조와 책임

### 3.1 루트

- `run.py`
  - 루트 실행용 래퍼
  - `src/`를 `sys.path`에 주입한 뒤 `pipeline.main()` 호출
- `README.md`
  - 목적, 사용법, 아키텍처 설명
- `requirements.txt`
  - 현재 의존성: `requests`, `beautifulsoup4`, `playwright`
- `data/site_url_list.txt`
  - 샘플 입력 URL 목록

### 3.2 핵심 모듈

- `src/pipeline.py`
  - 실제 CLI 진입점
  - 파이프라인 단계 정의 및 실행 순서 관리
  - URL 병렬 평가 오케스트레이션
- `src/config.py`
  - 평가/수집/병렬/Playwright/스코어링 전역 설정
- `src/models.py`
  - `FetchResult`, `CriterionResult`, `EvaluationResult` 등 핵심 데이터 구조
- `src/utils.py`
  - URL 정규화, 키워드 탐지, 링크/정책/pricing 힌트 판별
- `src/keywords.py`
  - AI/비AI/카테고리/서브태스크/플랫폼/정책 관련 키워드 사전

### 3.3 수집 및 평가 모듈

- `src/fetchers/page_fetcher.py`
  - `requests`와 `Playwright`를 혼합 사용하는 fetcher
- `src/classifiers/discovery_signals.py`
  - 후보 URL 수집과 구조화 신호 추출
- `src/classifiers/ai_scope_classifier.py`
  - AI 사이트 여부를 판정하는 게이트
- `src/classifiers/taxonomy_classifier.py`
  - primary category, sub-task, meta category, platform, pricing model 추정
- `src/classifiers/criteria_evaluator.py`
  - 5개 품질 기준 평가와 weighted 상태 판정
- `src/classifiers/status_policy.py`
  - review gate 및 최종 summary 생성

## 4. 실행 방식

사용자는 루트에서 `python run.py ...` 형태로 실행한다.

지원 입력 형태:

- URL 하나
- URL 여러 개
- `.txt` 파일 경로
- `--url-file <path>`

`pipeline._collect_urls_from_cli()`는 입력 인자를 순회하면서:

- `--url-file` 뒤의 텍스트 파일을 읽고
- `.txt` 확장자이면서 실제 파일이면 URL 목록 파일로 간주하며
- 그 외는 URL 문자열로 취급한다.

그 뒤 순서를 보존한 채 중복 제거를 수행한다.

이 설계의 의미:

- 배치 입력과 직접 입력을 같은 엔트리포인트에서 처리한다.
- URL 리스트를 미리 텍스트 파일로 관리하기 쉽다.
- 중복 URL 평가를 한 번만 수행한다.

## 5. 전체 파이프라인의 실제 흐름

현재 기본 파이프라인 단계는 아래 순서로 고정돼 있다.

1. `step_fetch_and_collect_pages`
2. `step_extract_signals`
3. `step_assess_ai_scope`
4. `step_classify_taxonomy`
5. `step_evaluate_criteria`
6. `step_score_and_predict_status`
7. `step_review_and_finalize_status`
8. `step_build_summary`

즉, 이 시스템은 먼저 페이지를 모아놓고, 그 결과를 공유 텍스트 캐시로 압축한 다음, AI 사이트 여부를 먼저 판정하고, 그 결과를 바탕으로 taxonomy와 품질 평가를 수행한다.

이 순서는 중요하다.

- `ai_scope`가 `non_ai`이면 taxonomy 상세 분류와 criteria가 사실상 평가 제외 모드로 들어간다.
- taxonomy는 AI 판정 결과를 참고한다.
- review gate는 criteria와 anti-bot 신호를 모두 참고한다.

## 6. 데이터 모델

### 6.1 `Evidence`

판정 근거의 최소 단위다.

구성:

- `url`
- `snippet`
- `label`

즉, 각 criteria는 “왜 그렇게 판단했는지”를 URL+스니펫으로 남길 수 있다.

### 6.2 `CriterionResult`

단일 품질 기준의 결과다.

구성:

- `name`
- `passed`
- `reason`
- `confidence`
- `evidence`

이 구조 때문에 이 프로젝트는 단순 boolean 판정이 아니라, 근거 기반 반구조화 결과를 생성한다.

### 6.3 `FetchResult`

단일 페이지 수집 결과다.

구성:

- 요청 URL / 최종 URL
- 상태코드
- 성공 여부
- 원본 HTML
- 정제된 텍스트
- 제목
- 메타 설명
- 추출 링크 목록
- 에러 문자열
- `fetched_by` (`requests` 또는 `playwright`)

즉, 후속 classifier들은 원시 HTML이 아니라 `FetchResult`를 기반으로만 동작한다.

### 6.4 `EvaluationResult`

최종 평가 결과다.

구성:

- 입력 URL
- 정규화 URL
- `predicted_status`
- `final_status`
- `passed_count`
- `hard_pass`
- `review_required`
- `review_reasons`
- `criteria`
- `summary`
- `extracted`
- `total_score`
- `score_breakdown`

최종 출력은 `to_dict()`를 통해 JSON 직렬화 가능 구조로 변환된다.

## 7. 수집 계층: `PageFetcher`

이 프로젝트의 수집 로직은 단순 `requests.get()`가 아니다.  
핵심은 `requests` 결과를 기본값으로 쓰되, 필요할 때만 `Playwright`를 재시도하는 혼합 전략이다.

### 7.1 기본 정책

`fetch(url)`의 동작은 다음과 같다.

- URL 정규화
- 우선 `requests` 수집
- 결과가 빈약하거나 챌린지 페이지면 Playwright 재수집
- 둘 다 있으면 더 풍부한 결과를 선택

### 7.2 URL 정규화

`normalize_url()`은 다음 처리를 한다.

- 스킴이 없으면 `https://` 추가
- 호스트를 소문자로 통일
- path가 없으면 `/`
- trailing slash 정리
- query string, fragment는 제거

이 의미는 크다.

- 동일 리소스라도 query string이 다르면 같은 URL로 취급된다.
- 추적 파라미터가 많은 사이트에서는 중복 제거에 유리하다.
- 반대로 query string이 핵심인 페이지는 손실될 수 있다.

### 7.3 `requests` 수집

정적 수집은 `requests.Session` 기반이다.

특징:

- 스레드별 session 사용
- HTTPAdapter + Retry 설정
- `429`, `500`, `502`, `503`, `504` 재시도
- GET/HEAD만 재시도 허용
- 브라우저 형태의 User-Agent 사용

### 7.4 `Playwright` 사용 조건

`_needs_playwright()`가 requests 결과 품질을 기준으로 재수집 필요 여부를 판단한다.

Playwright 재수집 조건:

- `requests` 결과가 실패
- anti-bot challenge로 보임
- 본문 길이와 링크 수가 모두 빈약
- JS 앱 시그널이 있고 본문 또는 링크가 빈약

candidate page의 lightweight fetch에서는 기준이 더 보수적이다.

- `requests`가 성공했고
- challenge 징후가 없고
- JS 앱 + 매우 빈약한 본문이 아닐 경우
- 그냥 `requests` 결과를 사용한다.

즉, 홈페이지는 비교적 적극적으로 Playwright를 쓰지만, 후보 페이지는 속도 우선으로 설계돼 있다.

### 7.5 Playwright 브라우저 설정

설정값 기반으로 다음을 제어한다.

- 브라우저 종류: 기본 `chromium`
- headless 여부: 기본 `False`
- timeout
- `wait_until`
- 추가 대기 시간
- anti-bot challenge 대기 시간과 재시도 횟수
- 사용자 에이전트

추가 동작:

- `navigator.webdriver` 제거 스크립트 주입
- `Accept-Language` 설정
- 일반 쿠키 배너/모달 닫기 시도
- 자동 스크롤 수행

즉, 동적 렌더링뿐 아니라 anti-bot 우회와 lazy-loading 대응까지 고려한 fetcher다.

### 7.6 anti-bot 감지

`PageFetcher.is_challenge_text()`는 아래 시그널을 감지한다.

- `just a moment`
- `checking your browser`
- `cloudflare`
- `captcha`
- `__cf_chl`
- `/cdn-cgi/challenge-platform/`

챌린지 결과면:

- Playwright는 일정 시간 기다렸다가 재확인
- 계속 챌린지면 `anti_bot_challenge_detected`
- downstream 평가기에서 이 신호를 별도 review reason으로 사용

### 7.7 결과 선택 기준

`requests`와 `Playwright` 결과가 모두 있으면 `_choose_better_result()`가 선택한다.

우선순위:

- 성공/실패 여부
- challenge 여부
- 풍부도 점수

풍부도 점수는 대략 다음 요소를 더한다.

- 본문 길이
- 링크 수
- title 존재
- meta description 존재
- ok 여부

즉, “더 많이 읽힌 쪽”을 선택하는 전략이다.

## 8. 후보 URL 수집: `DiscoverySignalMixin`

홈페이지 하나만 보는 구조가 아니다.  
홈페이지 링크를 읽고 pricing/docs/policy/product 성격의 후보 페이지를 추가로 모은다.

### 8.1 후보 URL 종류

종류별 bucket:

- `pricing`
- `docs`
- `policy`
- `product`
- `probe`

### 8.2 수집 규칙

홈페이지가 정상 수집된 경우 링크를 순회하며:

- pricing 관련 링크 텍스트/URL이면 `pricing`
- docs/help 텍스트면 `docs`
- policy 텍스트면 `policy`
- feature/about/use case/platform 류면 `product`

같은 도메인이 아닌 외부 링크라도:

- docs host prefix 조건 충족 시 docs로 인정
- 특정 정책 host 조건 충족 시 policy로 인정

즉, 문서/정책이 외부 서브도메인에 있는 SaaS도 어느 정도 대응한다.

### 8.3 known-domain seed

`likely_related_external_candidates()`는 OpenAI/ChatGPT 계열 도메인에서:

- `https://chatgpt.com/pricing`
- `https://help.openai.com/en/`
- `https://openai.com/policies/row-privacy-policy/`

같은 추가 후보를 무조건 넣는다.

이건 강한 예외 처리다.  
즉, 특정 브랜드는 “홈페이지 링크 구조를 믿지 않고” 외부 근거 페이지를 보강한다.

### 8.4 fallback probe

홈페이지가 실패했거나, 충분한 후보를 못 모았으면 아래 probe path를 붙여본다.

- `/pricing`
- `/plans`
- `/docs`
- `/help`
- `/support`
- `/privacy`
- `/privacy-policy`
- `/terms`

즉, 링크를 못 읽어도 일반적인 SaaS 경로를 탐색한다.

### 8.5 구조화 신호 추출

후보 페이지까지 수집한 뒤 `extracted` dict를 만든다.

포함 신호:

- `homepage_accessible`
- `has_waitlist_signal`
- `has_positive_use_signal`
- `pricing_pages`
- `docs_pages`
- `policy_pages`
- `product_pages`
- `faq_only_docs`
- `contact_sales_only`
- `license_detected`
- `update_signal`
- `homepage_fetched_by`
- `anti_bot_blocked`
- `playwright_enabled`
- `playwright_disabled_reason`

이 `extracted`가 이후 거의 모든 판단의 공통 기반이다.

## 9. AI 사이트 판정: `AiScopeClassifierMixin`

이 프로젝트의 첫 번째 핵심 게이트다.

판정 결과:

- `ai`
- `uncertain`
- `non_ai`

즉, 단순 boolean이 아니라 경계 상태를 별도로 둔다.

### 9.1 입력 텍스트

기본적으로 홈페이지와 후보 페이지들의:

- 최종 URL
- title
- meta_description
- 본문 일부
- 링크 일부

를 합친 blob을 사용한다.

pipeline은 이를 위해 `_build_shared_text_cache()`를 먼저 만들어 재사용한다.

### 9.2 키워드 체계

키워드는 네 그룹으로 나뉜다.

- strong AI keywords
- weak AI keywords
- strong non-AI keywords
- weak non-AI keywords

점수식:

- `ai_signal_score = 2 * strong_ai + weak_ai`
- `non_ai_signal_score = 2 * strong_non_ai + weak_non_ai`
- `margin = ai_signal_score - non_ai_signal_score`

### 9.3 보정 규칙

추가 보정이 있다.

- 독립 토큰 `ai`는 weak AI hit로 추가
- 도메인에 `openai`, `anthropic`, `huggingface` 등 브랜드 힌트가 있으면 가산
- `.ai` TLD도 약한 보조 신호로 사용

### 9.4 판정 규칙

강한 AI 판정 조건:

- strong AI hit가 2개 이상이고 margin이 양수
- 또는 strong AI 1개 + weak AI 또는 양수 margin + non-AI 점수 낮음

약한 AI 다수 판정 조건:

- strong AI는 없지만
- explicit weak hit가 있고
- weak AI가 3개 이상이며
- margin이 충분히 크고
- non-AI 점수가 낮음

브랜드 판정 조건:

- known AI brand domain이고
- 일부 AI 신호 또는 낮은 non-AI 점수

`.ai` 도메인 조건:

- `.ai` TLD이고
- strong AI 또는 약한 AI 조합이 존재

경계 구간:

- margin이 설정 범위 안에 있고
- non-AI 점수가 너무 높지 않으면 `uncertain`

그 외:

- `non_ai`

### 9.5 이 설계의 의미

장점:

- 뉴스/쇼핑/커뮤니티 같은 비대상 사이트를 조기에 걸러낼 수 있다.
- AI 브랜드 도메인에 대한 보정이 있다.
- 애매한 사이트를 `uncertain`으로 따로 보류한다.

한계:

- 키워드가 빈약한 고급 B2B 사이트는 과소평가될 수 있다.
- `.ai` 도메인과 브랜드 힌트는 오탐 위험도 있다.
- 콘텐츠 언어가 다양할 경우 키워드 사전 품질에 크게 의존한다.

## 10. taxonomy 분류: `TaxonomyClassifierMixin`

AI 사이트로 간주된 경우에만 상세 taxonomy를 계산한다.

`non_ai`이면 결과는 사실상 “taxonomy skipped” 형태다.

### 10.1 primary category

각 primary category별 키워드 집합에 대해:

- 본문 hit
- header hit
- 링크 hit

를 서로 다른 가중치로 합산한다.

점수식:

- body hits = 1배
- header hits = 1.5배
- link hits = 0.7배

가장 높은 점수를 primary category로 선택한다.

후보:

- Writing & Docs
- Coding
- Research
- Design & Creative
- Data & Analytics
- Ops & Automation
- Meeting & Sales
- DevOps / Security

상위 점수가 1.0 미만이면 `Uncategorized`.

### 10.2 primary confidence

top score와 second score의 margin을 함께 써서 confidence를 만든다.

즉, 단순 최고점뿐 아니라 “다른 카테고리와 얼마나 차이나는가”도 반영한다.

### 10.3 sub-task

선택된 primary category에 해당하는 subtask 키워드 집합만 평가한다.

그 후 hit 수 상위 항목을 `config.max_sub_tasks`까지 반환한다.

중요한 의미:

- sub-task는 전 카테고리 공통 탐색이 아니다.
- 먼저 primary category가 잘못 잡히면 sub-task도 연쇄적으로 왜곡된다.

### 10.4 meta category

별도의 메타 키워드로:

- Create
- Analyze
- Build
- Automate
- Communicate
- Secure

를 산출한다.

hit가 없으면 primary category별 default meta를 사용한다.

### 10.5 one-line summary

우선순위:

- homepage meta description이 충분히 길면 그것을 사용
- 아니면 본문 첫 문장 후보를 사용
- 그것도 없으면 title/본문 일부

즉, summary 생성은 별도 LLM 요약이 아니라 스니펫 기반이다.

### 10.6 platform 추정

platform 후보:

- web
- mobile
- desktop
- browser_extension
- slack
- vscode
- api

특징:

- 수집 성공 페이지가 하나라도 있으면 `web`은 기본 포함
- URL host/path 힌트로 mobile, extension, desktop 보정
- keyword나 `/api` 힌트로 `api` 판단

### 10.7 pricing model 추정

출력값 예:

- `open_source_license`
- `free_and_paid`
- `paid_plus_contact_sales`
- `paid`
- `contact_sales_only`
- `free`
- `unknown`

이 값은 state를 직접 결정하진 않지만, taxonomy 결과의 설명력을 높인다.

## 11. criteria 평가: `CriteriaEvaluatorMixin`

이 프로젝트의 두 번째 핵심이다.  
AI 사이트로 인정된 후보에 대해 5개 기준을 평가한다.

5개 기준:

1. `usable_now`
2. `clear_function_desc`
3. `has_pricing`
4. `has_docs_or_help`
5. `has_privacy_or_data_policy`

### 11.1 non-AI 사이트 처리

`ai_scope`가 `non_ai`이면 5개 criteria를 모두 `passed=False`로 채운다.

즉, 이 경우는 “평가 실패”가 아니라 “평가 대상 제외”에 가깝다.

reason도 `AI 사이트 판별 게이트에서 제외됨`으로 통일된다.

### 11.2 `usable_now`

이 기준은 “지금 실제로 사용 가능한 서비스인가”를 본다.

판정 신호:

- positive use text
- 같은 도메인 내 usable URL hint
- docs 페이지에 install/quickstart/self-hosted 등 OSS 설치 신호

반대로:

- waitlist
- coming soon
- early access

같은 negative signal만 있고 positive signal이 없으면 실패한다.

특이점:

- 홈페이지가 차단되어도 대체 페이지에서 사용/설치 경로가 있으면 통과 가능
- anti-bot으로 홈페이지 접근 실패 시 별도 reason을 준다

즉, SaaS뿐 아니라 self-hosted OSS도 사용 가능성으로 인정하려는 설계다.

### 11.3 `clear_function_desc`

가장 흥미로운 기준이다.  
문장 후보를 모아서 점수화한다.

문장 점수 구성:

- 길이
- action keyword 포함
- task noun 포함
- `for`, `helps`, `allows you to`, `위한`, `도와` 같은 설명 구조
- generic marketing phrase면 감점
- AI/agent/assistant 표현 소폭 가점

best sentence를 하나 고른 뒤:

- 점수 0.55 이상이면 통과
- 아니면 “마케팅 문구는 있으나 구체 기능 설명으로 보기 어려움”

LLM 보조:

- `enable_llm_for_clear_desc=True`
- 그리고 점수가 0.35 이상 0.75 미만

일 때만 `DummyLLM` 또는 실제 LLM 인터페이스를 타게 설계돼 있다.

하지만 현재 CLI는 `use_llm=False`로 실행하므로 기본적으로 LLM은 사용되지 않는다.

### 11.4 `has_pricing`

통과 조건:

- strong pricing page가 존재
- 또는 contact sales를 pricing으로 인정하도록 config가 켜짐
- 또는 OSS license를 pricing 근거로 인정

현재 기본 설정:

- `contact_sales_counts_as_pricing = False`
- `license_counts_as_pricing_for_oss = True`

즉:

- 문의만 있으면 기본적으로 pricing 실패
- 오픈소스 라이선스는 제한적으로 pricing 대체로 인정

### 11.5 `has_docs_or_help`

통과 조건:

- `docs_pages`가 존재

단, FAQ만 있고 정식 docs/help가 아닌 경우:

- `faq_counts_as_docs=False`면 실패 가능

현재 기본은 `True`이므로 FAQ-only도 docs로 인정된다.

### 11.6 `has_privacy_or_data_policy`

통과 조건:

- privacy/data policy/gdpr/dpa/개인정보 성격 문서 존재

terms만 있는 경우:

- `terms_only_counts_as_policy=True`면 통과
- 아니면 실패

현재 기본은 `True`다.

즉, 현재 정책은 비교적 완화돼 있다.

## 12. weighted score와 상태 예측

실제 상태 판정은 count 기반 기본 정책이 아니라 `WeightedQualityEvaluator`가 override한 weighted 정책을 사용한다.

### 12.1 가중치

- `usable_now = 0.30`
- `clear_function_desc = 0.25`
- `has_docs_or_help = 0.20`
- `has_privacy_or_data_policy = 0.20`
- `has_pricing = 0.05`

의미:

- 사용 가능성과 설명 명확성을 가장 중요하게 본다.
- pricing은 낮은 가중치다.

### 12.2 점수 계산 방식

기준별 점수는:

- passed면 `confidence`
- failed면 `0`

이다.

즉, failed criterion의 confidence는 점수에 반영되지 않는다.

총점은 `base * weight * 100`의 합으로 계산된다.

### 12.3 하한 게이트

아래를 못 넘으면 즉시 `rejected`다.

- `usable_now >= 0.60`
- `clear_function_desc >= 0.50`

즉, 문서/정책이 좋아도 “실사용 가능성”과 “기능 설명”이 약하면 탈락한다.

### 12.4 상태 규칙

- `total_score >= 85`
  - 그리고 docs score >= 0.30
  - 그리고 privacy score >= 0.30
  - 이면 `curated`
- `total_score >= 65`
  - 이면 `incubating`
- 그 외 `rejected`

즉, curated는 총점뿐 아니라 docs/policy 하한도 추가로 요구한다.

### 12.5 anti-bot 예외

파이프라인 단계에서:

- `anti_bot_blocked=True`
- `homepage.ok=False`
- `passed_count==0`
- `predicted_status=="rejected"`

이면 강제로 `predicted_status="incubating"`로 올린다.

즉, anti-bot 때문에 아무 것도 못 읽은 사이트를 완전 탈락시키지 않도록 한 완충 장치다.

## 13. review gate와 최종 상태

`predicted_status`가 끝이 아니다.  
그 다음 review gate가 들어가 `final_status`를 확정한다.

review 사유 생성 조건:

- `ai_scope == uncertain`
- `clear_function_desc.confidence < 0.75`
- `contact_sales_only`
- `faq_only_docs`
- `anti_bot_blocked`
- requests만 사용했고 Playwright로 재수집하지 않았는데 anti-bot 징후가 있거나 content가 빈약함
- curated 후보인데 docs evidence 부족
- curated 후보인데 policy evidence 부족

특히 중요:

- `curated_requires_no_review = True`

이므로 curated 후보라도 review가 필요하면 최종 상태는 `incubating`으로 내려간다.

그리고 review reason에 `curated 후보였지만 수동 검수 전 보류`가 추가된다.

즉, 이 시스템에서 `curated`는 “점수만 높으면 되는 상태”가 아니라 “review-free 상태”다.

## 14. 병렬 처리 구조

병렬성은 두 층에 있다.

### 14.1 URL 병렬 평가

입력 URL이 여러 개이고 설정이 켜져 있으면:

- `ThreadPoolExecutor`
- 기본 worker 수 `3`

로 각 URL을 병렬 평가한다.

각 워커는 thread-local evaluator를 하나씩 가진다.

즉:

- fetcher도 워커별
- Playwright context도 워커별
- requests session도 워커별

이라서 스레드 간 상태 충돌을 줄이려는 설계다.

### 14.2 후보 페이지 병렬 fetch

한 URL 내부에서도 후보 페이지를 병렬 수집할 수 있다.

기본 worker 수는 `4`지만, URL 병렬과 중첩될 경우 자동 축소된다.

자동 축소 규칙:

- `candidate_workers // url_evaluation_workers`
- 최소 1
- 다만 후보가 여러 개인데 1로 고정되면 2까지 보정

즉, 중첩 병렬 때문에 전체 스레드 수가 과도하게 늘어나는 것을 막으려는 장치다.

### 14.3 지연 정책

- URL 간 지연은 기본 `0.05초`
- 다만 URL 병렬 모드에서는 기본적으로 생략

즉, 단일 실행은 약간 완만하게, 병렬 실행은 처리량 우선이다.

## 15. shared text cache의 역할

`pipeline._build_shared_text_cache()`는 다음 블롭을 미리 만든다.

- `corpus`
- `header_blob`
- `links_blob`
- `combined_blob`
- `ai_scope_blob`

이 캐시는 AI 스코프 판정과 taxonomy 분류가 같은 텍스트를 반복 계산하지 않게 한다.

이 설계는 두 가지 장점이 있다.

- 동일 텍스트 전처리 반복 감소
- 서로 다른 classifier가 같은 입력 기반으로 동작

즉, classifier 간 일관성을 높인다.

## 16. 출력 구조

최종 출력은 URL별 `EvaluationResult.to_dict()` 리스트를 JSON 파일로 저장한다.

결과 JSON에는 다음 성격의 정보가 함께 들어간다.

- 최종 상태값
- 점수
- review 필요 여부
- 5개 criterion 상세
- 근거 evidence
- extracted 신호
- taxonomy와 ai_scope 결과

즉, 단순 스코어가 아니라 “왜 이런 결론이 나왔는지”를 어느 정도 추적 가능한 분석 결과물이다.

## 17. 구현상 강점

### 17.1 수집과 평가의 분리

fetch 결과가 `FetchResult`로 정규화된 뒤 classifier가 동작하므로 구조가 비교적 명확하다.

### 17.2 anti-bot 현실 대응

Cloudflare/challenge 감지와 Playwright fallback이 이미 들어가 있다.

### 17.3 단순 count가 아닌 weighted scoring

모든 criterion을 동일 비중으로 보지 않는다.

### 17.4 `uncertain` 상태 도입

애매한 AI 사이트를 억지로 긍정/부정 이분법으로 넣지 않는다.

### 17.5 review gate 존재

점수만 높아도 근거가 불안하면 curated로 확정하지 않는다.

## 18. 구현상 약점과 리스크

### 18.1 테스트 범위의 한계

현재 `tests/`는 추가됐지만 범위가 제한적이다.  
즉, 키워드 조정이나 fetch 정책 변경 전반을 회귀 검증하려면 대표 사이트셋 기반 테스트를 더 확장해야 한다.

### 18.2 규칙 기반 과적합 가능성

특정 SaaS 패턴에는 잘 맞지만, 카피가 독특한 사이트나 비영어권 사이트에서는 오판 가능성이 높다.

### 18.3 `normalize_url()`의 query 제거

쿼리스트링이 실질적 리소스 차이를 만드는 사이트에서는 의도치 않은 정보 손실이 발생할 수 있다.

### 18.4 keyword 사전 유지보수 비용

`keywords.py`가 방대하고, 핵심 로직이 이 파일에 강하게 의존한다.  
운영 중 성능보다 사전 품질 관리가 더 큰 병목이 될 가능성이 높다.

### 18.5 known-domain 예외 처리의 확장성

OpenAI/ChatGPT처럼 특정 브랜드에 대한 하드코딩 seed는 당장은 유용하지만, 브랜드별 예외가 늘어나면 일반화가 무너질 수 있다.
현재 코드(`likely_related_external_candidates`)에 known-domain seed가 남아 있으므로 이 리스크는 여전히 유효하다.

### 18.6 output 채널이 단일 JSON 파일 중심

현재는 DB 저장, 캐시, 재시도 큐, 중간 산출물 다중 보존이 없다.

### 18.7 LLM 인터페이스는 사실상 비활성

`DummyLLM` 인터페이스는 있으나 현재 CLI에서는 사용되지 않는다.

## 19. 운영 관점에서 이해해야 할 핵심 포인트

이 프로젝트를 한 줄로 요약하면:

“후보 URL을 받아, 공개 웹페이지에서 확인 가능한 신호만으로 AI 서비스 여부와 품질을 규칙 기반으로 평가하는 로컬 JSON 파일 출력 파이프라인”

운영자가 반드시 이해해야 하는 포인트:

- 이 코드는 웹 전체를 탐색하지 않는다. 후보 URL을 평가한다.
- AI 사이트 여부를 먼저 막고, 그 다음 taxonomy/quality를 평가한다.
- `curated`는 단순 고득점이 아니라 review-free 상태여야 한다.
- anti-bot 때문에 정보를 못 읽은 사이트는 완전 탈락 대신 `incubating` 완충이 가능하다.
- taxonomy 정확도는 primary category 정확도에 크게 의존한다.
- 분류 품질은 결국 `keywords.py`와 공개 페이지 품질에 크게 의존한다.

## 20. 개선 우선순위 제안

현재 구조를 유지하면서 개선 효과가 큰 항목은 아래 순서다.

1. 테스트 범위 확장(대표 사이트셋 기반 회귀 케이스 추가)
2. 대표 사이트셋 고정 후 회귀 검증 체계 구축
3. `keywords.py`를 도메인별/언어별 세분화
4. fetch 결과 캐시 도입
5. output 파일 저장과 중간 산출물 보존
6. LLM 보조 판정을 옵션이 아니라 통제된 보조 단계로 재설계
7. known-domain 예외를 설정 파일/룰셋으로 외부화

## 21. 툴 관리 체계 기획

현재 파이프라인은 “개별 URL 평가기”로는 충분히 유용하지만, 운영 관점에서는 평가 결과를 지속적으로 관리하는 별도 툴 관리 체계가 필요하다.

권장 방향은 아래와 같다.

### 21.1 관리 단위

기본 관리 단위는 `tool` 하나와 그에 연결된 `canonical_url` 하나다.

권장 필드:

- `tool_id`
- `display_name`
- `canonical_url`
- `aliases`
- `source` (수집 출처)
- `first_seen_at`
- `last_checked_at`
- `current_status`
- `current_taxonomy`
- `current_score`
- `review_required`
- `review_notes`

즉, 현재 JSON 결과를 일회성 산출물로만 두지 말고, “도구 레지스트리의 최신 스냅샷”으로 흡수할 수 있어야 한다.

### 21.2 상태 수명주기

운영 상태는 최소한 아래 단계로 나누는 것이 좋다.

1. `discovered`
2. `screened`
3. `incubating`
4. `curated`
5. `rejected`
6. `archived`

의미:

- `discovered`: 아직 평가 전인 신규 후보
- `screened`: 1회 이상 자동 평가 완료
- `incubating`: AI 가능성은 있으나 수동 검토 또는 보강 필요
- `curated`: 운영 리스트에 올릴 수 있는 확정 상태
- `rejected`: 비대상 또는 기준 미달
- `archived`: 서비스 종료, 리브랜딩, 중복 병합 등으로 비활성화

현재 코드의 `predicted_status`와 `final_status`는 이 수명주기 안의 일부 상태를 채우는 입력값으로 보는 것이 적절하다.

### 21.3 변경 이력 관리

툴 관리는 “현재 상태”보다 “왜 바뀌었는지”가 더 중요하다.

최소 이력 항목:

- 평가 실행 시각
- 입력 URL
- 최종 URL
- 점수 변화
- status 변화
- taxonomy 변화
- review reason 변화
- 사용된 규칙 버전

즉, 같은 서비스가 정책/가격/문서 구조를 바꿨을 때 상태가 왜 바뀌었는지 추적 가능해야 한다.

### 21.4 수동 검수 큐

아래 조건은 별도 검수 큐로 보내는 것이 좋다.

- `ai_scope = uncertain`
- `review_required = true`
- anti-bot으로 본문 수집 실패
- taxonomy confidence 낮음
- 이전 평가 대비 status 급변

검수 큐에는 자동 결과만이 아니라 근거 evidence, candidate page 목록, 이전 평가 대비 diff를 함께 보여주는 방식이 적합하다.

### 21.5 중복과 canonicalization

도메인/브랜드 기준 중복 관리가 필요하다.

예:

- `chatgpt.com`
- `openai.com/chatgpt`
- 국가별 랜딩 URL
- 가격/문서 서브도메인

운영 체계에서는 이를 별도 페이지로 취급하지 말고 하나의 canonical tool 아래로 묶어야 한다.

즉, 현재 `normalize_url()`은 URL 정규화용이고, 운영 레벨의 canonicalization 문제까지 해결하지는 않는다.

### 21.6 규칙과 예외 관리

현재는 known-domain seed, 외부 docs/policy 허용 규칙, 키워드 사전이 코드에 들어 있다.

운영 단계에서는 아래처럼 분리하는 편이 좋다.

- 일반 규칙: 코드 또는 버전된 룰셋
- 브랜드 예외: 별도 설정 파일
- 수동 오버라이드: 운영자 입력 레이어

이렇게 하면 “코드 수정이 필요한 변경”과 “운영 정책 조정만 필요한 변경”을 분리할 수 있다.

### 21.7 재평가 정책

모든 툴을 같은 주기로 재평가할 필요는 없다.

권장 전략:

- `curated`: 느린 주기 재평가
- `incubating`: 빠른 주기 재평가
- anti-bot 실패 건: 짧은 backoff 후 재시도
- `rejected`: 장기 주기 또는 수동 재검토 시만 재실행

즉, 상태별 재평가 cadence를 다르게 두는 것이 운영 비용 대비 효율이 높다.

### 21.8 운영 지표

툴 관리 체계가 자리 잡으면 아래 지표를 봐야 한다.

- 상태별 툴 수
- 신규 discovered 수
- curated 전환율
- uncertain 비율
- anti-bot 실패율
- 수동 검수 backlog
- 규칙 변경 후 상태 변동률

이 지표들이 있어야 규칙 품질 저하나 수집 안정성 악화를 조기에 감지할 수 있다.

### 21.9 적용 현황 (2026-04-12)

현재 코드 기준 반영 내용:

- 결과 JSON에 `management` 스냅샷 필드 추가
- `tool_id`, `canonical_url`, `aliases`, `source`, `first_seen_at`, `last_checked_at` 기록
- `lifecycle_state`, `current_status`, `current_taxonomy`, `current_score` 기록
- 검수 큐 기준 태그(`review_queue_reasons`) 자동 생성
- 상태/차단 여부 기반 재평가 우선순위(`reevaluation_priority`) 계산
- `result/tool_registry.json`에 도구별 최신 상태 + `change_history` 누적 저장

현재 범위에서 아직 미반영인 항목:

- `discovered` 상태의 별도 수집 단계 분리
- `archived` 전환 자동화
- 운영자 수동 오버라이드 레이어(UI/DB)

## 22. 결론

`ai_url_classifier`는 현재 상태에서도 구조가 비교적 선명하다.

- 엔트리포인트는 단순하다.
- fetch 계층은 현실적인 anti-bot/JS 대응을 갖고 있다.
- classifier는 `AI 스코프`, `taxonomy`, `criteria`, `status`, `review`로 책임이 분리돼 있다.
- 최종 출력은 사람이 검수 가능한 evidence 중심 JSON이다.

반면, 이 시스템의 정확도와 유지보수성은 결국 다음에 달려 있다.

- 키워드 사전 품질
- 대표 사이트셋 기반 회귀 테스트
- 예외 규칙의 확장 방식
- 네트워크/anti-bot 환경에서의 수집 안정성

즉, 현재 코드는 “MVP를 넘은 규칙 기반 평가기”지만, 운영 품질을 높이려면 테스트와 룰 관리 체계가 다음 단계의 핵심이다.

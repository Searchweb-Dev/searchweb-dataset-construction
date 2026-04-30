# Architecture

## 파이프라인 흐름

```
1. URL 입력
2. 홈페이지 + 후보 페이지 수집      (requests → Playwright fallback)
3. 공용 텍스트 블롭 생성            (분류기 간 재파싱 방지)
4. AI 스코프 판정                   → ai / uncertain / non_ai
5. Taxonomy 분류                    (scope == ai 일 때만)
6. 5개 품질 기준 평가
7. Weighted score → predicted_status
8. Review gate → final_status 확정
9. JSON 저장                        (results_*.json, tool_registry.json)
```

---

## 모듈 구조

```
src/
├── pipeline.py               # CLI 진입점, 단계 함수 조합, 병렬 URL 평가
├── config.py                 # EvalConfig — 가중치, 임계값, 워커 수
├── models.py                 # FetchResult, CriterionResult, EvaluationResult, DummyLLM
├── keywords.py               # AI/non-AI 강약 키워드 사전
├── utils.py                  # 텍스트 정규화, 도메인 추출
├── fetchers/
│   └── page_fetcher.py       # 혼합 fetch + 후보 페이지 탐색
└── classifiers/
    ├── ai_scope_classifier.py    # AI 스코프 게이트 (Mixin)
    ├── taxonomy_classifier.py    # primary_category / sub_tasks 분류
    ├── criteria_evaluator.py     # 5개 기준 평가 + weighted score
    ├── status_policy.py          # 상태 예측, review gate, summary 생성 (Mixin)
    └── discovery_signals.py      # 구조화 신호 추출 (CTA, pricing, docs, policy)
```

---

## 상태 모델

`scope_decision`은 출력값이 아닌 **흐름 제어 신호**다.

```
scope_decision  →  ai | uncertain | non_ai

predicted_status
  ├─ curated    (score >= 85, 하한 게이트 통과)
  ├─ incubating (score >= 65)
  └─ rejected   (score < 65)

final_status  ← predicted_status + review gate 적용
  ├─ curated    = predicted curated AND review 없음
  ├─ incubating = score >= 65, 또는 review gate에 걸린 curated
  └─ rejected   = score < 65
```

> `predicted_status == curated`라도 review gate에 걸리면 `final_status`는 `incubating`으로 내려간다.

---

## AI 스코프 게이트

taxonomy/품질 평가 전에 먼저 실행해 불필요한 평가를 생략한다.

**점수식**

```
ai_signal_score     = 2 × strong_ai  + weak_ai
non_ai_signal_score = 2 × strong_non_ai + weak_non_ai
margin              = ai_signal_score - non_ai_signal_score
```

**보조 신호**: known AI brand domain, `.ai` TLD

`non_ai` 판정 시 taxonomy 분류와 품질 평가는 제외 모드로 들어간다.

---

## Taxonomy 분류

`scope_decision == ai`일 때만 실행된다. primary category가 틀리면 sub_tasks도 연쇄적으로 왜곡된다.

| 출력 필드 | 설명 |
|---|---|
| `primary_category` | Writing & Docs / Coding / Research / Design & Creative / Data & Analytics / Ops & Automation / Meeting & Sales / DevOps & Security |
| `sub_tasks` | primary category 안에서만 평가 |
| `meta_categories` | 복수 카테고리 교차 레이블 |
| `platforms` | Web / API / CLI / Mobile 등 |
| `pricing_model` | Free / Freemium / Paid / OSS 등 |
| `one_line_summary` | 한 줄 요약 |

---

## 품질 평가 기준

| criterion | 가중치 | 판정 기준 |
|---|---|---|
| `usable_now` | **0.30** | CTA·usable URL·install 신호 존재 여부 (waitlist/coming soon은 부정 신호) |
| `clear_function_desc` | **0.25** | "누구를 위해 무엇을 어떻게" 설명이 구체적인지 |
| `has_docs_or_help` | **0.20** | docs/help/guide/faq 페이지 존재 여부 (FAQ only 인정) |
| `has_privacy_or_data_policy` | **0.20** | privacy/terms/security 문서 존재 여부 (terms only 인정) |
| `has_pricing` | **0.05** | pricing 페이지 또는 OSS 라이선스 신호 (contact sales only는 실패) |

**하한 게이트** (미달 시 curated 불가): `usable_now >= 0.60`, `clear_function_desc >= 0.50`

---

## 수집 전략

**fetch 우선순위**: `requests` → 결과 빈약 또는 challenge 페이지 감지 시 `Playwright` → 둘 다 성공 시 더 풍부한 결과 선택

**후보 페이지**: `pricing` / `docs` / `policy` / `product` / `probe`

probe fallback 경로: `/pricing`, `/plans`, `/docs`, `/help`, `/support`, `/privacy`, `/privacy-policy`, `/terms`

**anti-bot 대응**: Cloudflare/captcha 감지 시 `anti_bot_blocked` 신호 생성 → `incubating` 완충 처리 (정보 부족으로 인한 무조건 `rejected` 방지)

---

## 병렬 처리

| 레이어 | 워커 수 | 비고 |
|---|---|---|
| URL 목록 평가 | 3 | `url_evaluation_workers` |
| 후보 페이지 fetch | 4 | `candidate_fetch_workers` |

중첩 병렬 시 후보 워커 수는 자동 축소된다 (`auto_tune_nested_parallel`).

---

## LLM 연결 구조

모든 분류는 규칙 기반이다. LLM 연결 자리는 `clear_function_desc`에만 열려 있으며, 기본값은 `use_llm=False` + `DummyLLM` 스텁이다.

# feat_rule_classifier: 규칙기반 URL 분류기 통합

## 개요

`ai_url_classifier/` 디렉터리에 구현된 규칙기반 8단계 파이프라인을 `src/rule/` 서브패키지로 이식하고,
`CLASSIFIER_MODE` 환경변수(`llm` | `rule`, 기본값: `llm`)로 LLM 분석기와 규칙기반 분석기를 분기한다.
분기는 `src/ai/analyzer.py`의 `get_analyzer()`에서 처리되며, `analyze_task.py`와 `detector.py` 등 상위
호출자는 일체 수정하지 않는다. 규칙기반 분석기는 LLM 분석기와 동일한 인터페이스를 구현하고,
출력 dict는 `detector.py`의 `_validate_analysis()`를 통과하여 `AISite`, `AICategory`, `AITag` 스키마에
저장 가능해야 한다.

---

## 데이터 흐름

```
analyze_task.py
  └─ AIDetector.detect_and_save(url)          ← 변경 없음
       └─ get_analyzer()                       ← 분기 추가
            ├─ CLASSIFIER_MODE=llm (기본)
            │    └─ GeminiAnalyzer / ClaudeAnalyzer  (기존 동작 무변경)
            └─ CLASSIFIER_MODE=rule
                 └─ RuleAnalyzer.analyze_website(url)
                      ├─ PageFetcher (requests + Playwright 폴백)
                      ├─ 8단계 파이프라인 실행
                      │    step1: fetch_and_collect_pages
                      │    step2: extract_signals
                      │    step3: assess_ai_scope
                      │    step4: classify_taxonomy
                      │    step5: evaluate_criteria
                      │    step6: score_and_predict_status
                      │    step7: review_and_finalize_status
                      │    step8: build_summary
                      └─ EvaluationResult → _map_to_analysis_dict()
                           └─ dict {is_ai_tool, title, description,
                                   categories, tags, scores, confidence,
                                   analyzer="rule"}
                                ↓
                      _validate_analysis()     ← 검증 통과
                      _save_site()             ← AISite 저장
                      _save_categories_and_tags() ← AICategory, AITag 저장
```

### 핵심 출력 스키마 (analyze_website 반환 dict)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `is_ai_tool` | `bool` | 필수 | ai_scope == "ai"/"uncertain" → True, "non_ai" → False |
| `title` | `str` | 필수 | extracted.homepage_title → URL 호스트 폴백 |
| `description` | `str` | 필수 | one_line_summary (50자 이내) 또는 summary 앞 50자 |
| `confidence` | `float` | 필수 | ai_scope.confidence (0.0–1.0) |
| `categories` | `list[dict]` | 권장 | level_1/level_2/level_3/is_primary 포함 |
| `tags` | `list[str]` | 권장 | sub_tasks[:3] |
| `scores` | `dict` | 권장 | utility/trust/originality (정수 1–10) |
| `analyzer` | `str` | 권장 | 고정값 "rule" |

### 카테고리 매핑 테이블 (primary_category → level_1/level_2)

| primary_category | level_1 | level_2 |
|---|---|---|
| Writing & Docs | text | text-generation |
| Coding | code | code-generation |
| Research | text | research-assistant |
| Design & Creative | image | image-generation |
| Data & Analytics | data | data-analysis |
| Ops & Automation | business | workflow-automation |
| Meeting & Sales | business | meeting-assistant |
| Uncategorized / 미매핑 | other | general |

### 점수 계산 규칙

- `score_utility`: `round(total_score / 10)`, 범위 클램프 1–10
  - `total_score`는 `WeightedQualityEvaluator._build_score_context()`의 가중합 (0–100)
- `score_trust`: `round(has_privacy_or_data_policy.confidence * 10)`, 범위 클램프 1–10
  - criteria 상에서 `has_privacy_or_data_policy` 키의 CriterionResult.confidence 사용
- `score_originality`: 고정값 5

---

## 기능 목록

### 기능 1: src/rule/ 서브패키지 골격 생성

- **설명**: `ai_url_classifier/src/` 내부 모듈들을 `src/rule/` 아래에 이식한다.
  `ai_url_classifier/`는 수정하지 않는다. 기존 코드에서 상대 임포트(from config import ..., from models import ...)를
  절대 임포트(from src.rule.config import ..., from src.rule.models import ...)로 변환하고,
  `sys.path` 조작 없이 Python 패키지로 동작하도록 `__init__.py`를 배치한다.
- **입력**: `ai_url_classifier/src/` 디렉터리 구조
- **출력**: `src/rule/` 서브패키지
  ```
  src/rule/
  ├── __init__.py
  ├── config.py          (EvalConfig — ai_url_classifier/config.py 이식)
  ├── keywords.py        (키워드 상수 — ai_url_classifier/src/keywords.py 이식)
  ├── utils.py           (헬퍼 함수 — ai_url_classifier/src/utils.py 이식)
  ├── models.py          (FetchResult, EvaluationResult 등)
  ├── pipeline.py        (run_quality_pipeline, DEFAULT_PIPELINE_STEPS)
  ├── fetchers/
  │   ├── __init__.py
  │   └── page_fetcher.py
  └── classifiers/
      ├── __init__.py
      ├── ai_scope_classifier.py
      ├── criteria_evaluator.py
      ├── discovery_signals.py
      ├── status_policy.py
      └── taxonomy_classifier.py
  ```
- **검증 기준**:
  - `python -c "from src.rule.pipeline import run_quality_pipeline"` 가 오류 없이 실행된다.
  - `python -c "from src.rule.models import EvaluationResult"` 가 오류 없이 실행된다.
  - 임포트 그래프에 `ai_url_classifier/` 참조가 없다.

---

### 기능 2: RuleAnalyzer 클래스 구현

- **설명**: `src/rule/analyzer.py`에 `RuleAnalyzer` 클래스를 구현한다.
  이 클래스는 `analyze_website(url: str) -> dict` 메서드 하나를 외부에 노출하며,
  내부에서 `run_quality_pipeline()`을 호출한 후 `EvaluationResult`를 분석 dict로 변환한다.
  예외 발생 시 예외를 상위로 전파한다(흡수하지 않는다).
- **입력**: `url: str` — 정규화된 웹사이트 URL
- **출력**: `dict[str, Any]` — `_validate_analysis()` 통과 보장 스키마
  ```python
  {
      "is_ai_tool": bool,
      "title": str,          # 비어있지 않음 (최소 호스트명)
      "description": str,    # 빈 문자열 허용
      "confidence": float,   # 0.0 ≤ x ≤ 1.0
      "categories": [{"level_1": str, "level_2": str, "level_3": str, "is_primary": bool}],
      "tags": [str],         # 최대 3개
      "scores": {"utility": int, "trust": int, "originality": int},
      "analyzer": "rule",
  }
  ```
- **검증 기준**:
  - 반환 dict에 `is_ai_tool`, `title`, `description`, `confidence` 4개 필수 필드가 모두 존재한다.
  - `confidence`가 `float`이고 0.0–1.0 범위 내에 있다.
  - `title`이 빈 문자열이 아니다.
  - `analyzer` 값이 `"rule"`이다.
  - `AIDetector._validate_analysis(result)` 호출 시 `True`를 반환한다.

---

### 기능 3: EvaluationResult → 분석 dict 변환 (_map_to_analysis_dict)

- **설명**: `EvaluationResult` 객체를 `detector.py`가 기대하는 분석 dict로 변환하는 순수 함수.
  `RuleAnalyzer` 내부에 구현하되 독립적으로 테스트 가능하도록 분리한다.
- **입력**: `result: EvaluationResult` — 파이프라인 실행 완료 객체
- **출력**: 기능 2에서 명세한 dict
- **세부 변환 규칙**:
  - `is_ai_tool`: `ai_scope.scope_decision in ("ai", "uncertain")` → True, `"non_ai"` → False
  - `title`: `extracted.homepage_title` 사용, 없으면 URL 호스트명
  - `description`: `taxonomy.one_line_summary`[:50], 없으면 `extracted.homepage_title`[:50], 없으면 `""`
  - `confidence`: `ai_scope.confidence` (float), 없으면 0.5
  - `categories`: `taxonomy.primary_category`를 카테고리 매핑 테이블로 변환하여 단일 항목 리스트 반환
    - `taxonomy_skipped=True`이면 `[]` 반환
  - `tags`: `taxonomy.sub_tasks[:3]`, 없으면 `[]`
  - `scores.utility`: `max(1, min(10, round(result.total_score / 10)))`, `total_score`가 None이면 5
  - `scores.trust`: `max(1, min(10, round(criteria["has_privacy_or_data_policy"].confidence * 10)))`, 키 없으면 5
  - `scores.originality`: 고정 5
- **검증 기준**:
  - 단위 테스트에서 mock `EvaluationResult`를 주입하고 각 필드 값이 규칙대로 변환됨을 확인한다.
  - `scope_decision="non_ai"` → `is_ai_tool=False`
  - `scope_decision="uncertain"` → `is_ai_tool=True`
  - `taxonomy_skipped=True` → `categories=[]`
  - `total_score=50.0` → `scores.utility=5`
  - `total_score=None` → `scores.utility=5`
  - `has_privacy_or_data_policy.confidence=0.95` → `scores.trust=10` (round(9.5)=10)

---

### 기능 4: get_analyzer() 분기 확장

- **설명**: `src/ai/analyzer.py`의 `get_analyzer()`에 `CLASSIFIER_MODE` 환경변수 분기를 추가한다.
  `CLASSIFIER_MODE=rule`이면 `RuleAnalyzer` 인스턴스를 반환하고,
  그 외 값(또는 미설정)이면 기존 LLM 분기 로직을 그대로 실행한다.
  `analyze_task.py`, `detector.py` 등 상위 호출자는 수정하지 않는다.
- **입력**: 환경변수 `CLASSIFIER_MODE` (`"llm"` | `"rule"`, 기본값 `"llm"`)
- **출력**: `RuleAnalyzer` 또는 기존 LLM 분석기 인스턴스
- **검증 기준**:
  - `CLASSIFIER_MODE=rule` 환경 하에서 `get_analyzer()`가 `RuleAnalyzer` 인스턴스를 반환한다.
  - `CLASSIFIER_MODE=llm` 환경 하에서 `get_analyzer()`가 기존 분석기 인스턴스를 반환한다 (기존 동작 무변경).
  - `CLASSIFIER_MODE` 미설정 시 기존 LLM 분기가 실행된다.
  - `src/core/config.py`에 `get_classifier_mode()` 헬퍼가 추가된다.

---

### 기능 5: config.py 환경변수 헬퍼 추가

- **설명**: `src/core/config.py`에 `get_classifier_mode() -> str` 함수를 추가한다.
  `CLASSIFIER_MODE` 환경변수를 읽어 소문자로 정규화하며, 기본값은 `"llm"`이다.
  유효하지 않은 값(`"llm"`도 `"rule"`도 아닌 경우)이 들어오면 경고 로그를 출력하고 `"llm"`으로 폴백한다.
- **입력**: 환경변수 `CLASSIFIER_MODE`
- **출력**: `"llm"` 또는 `"rule"` 문자열
- **검증 기준**:
  - `CLASSIFIER_MODE` 미설정 → `"llm"` 반환
  - `CLASSIFIER_MODE=rule` → `"rule"` 반환
  - `CLASSIFIER_MODE=LLM` → `"llm"` 반환 (대소문자 정규화)
  - `CLASSIFIER_MODE=invalid` → `"llm"` 반환 + 경고 로그 출력

---

### 기능 6: 단위 테스트 작성

- **설명**: 기능 2–5의 핵심 로직을 검증하는 pytest 단위 테스트를 `tests/rule/` 디렉터리에 작성한다.
  DB 연결 없이 실행되도록 mock/stub을 활용한다.
- **입력**: 각 함수/클래스의 인터페이스
- **출력**: `tests/rule/` 아래 테스트 파일
  ```
  tests/rule/
  ├── __init__.py
  ├── test_map_to_analysis_dict.py   (기능 3 변환 규칙 검증)
  ├── test_get_classifier_mode.py    (기능 5 환경변수 헬퍼)
  └── test_get_analyzer_branching.py (기능 4 분기 로직)
  ```
- **검증 기준**:
  - `pytest tests/rule/ -v` 전체 통과
  - 기능 3 변환 규칙의 6개 케이스(non_ai/uncertain/taxonomy_skipped/total_score 등)가 각각 독립 테스트로 존재한다.
  - 기능 5의 4가지 입력 케이스(미설정/rule/대소문자/잘못된값)가 각각 독립 테스트로 존재한다.
  - 기능 4의 분기 로직이 `CLASSIFIER_MODE=rule` / `CLASSIFIER_MODE=llm` 각각 별도 테스트로 존재한다.
  - 외부 네트워크 호출 없이 실행된다 (run_quality_pipeline은 mock 처리).

---

## 구현 시 주의사항

1. **ai_url_classifier/ 수정 금지**: 원본 디렉터리는 읽기 전용으로 참조만 한다.
2. **상위 호출자 무수정**: `analyze_task.py`, `detector.py` 변경 없음.
3. **임포트 격리**: `src/rule/`은 `ai_url_classifier/`를 임포트해서는 안 된다.
4. **타입 힌트 완비**: 모든 공개 함수/메서드에 타입 어노테이션 필수.
5. **로깅**: `print()` 대신 `logging` 사용. 한국어 docstring 필수.
6. **예외 전파**: `RuleAnalyzer.analyze_website()`는 예외를 흡수하지 않는다. 상위 `AIDetector`가 처리.
7. **Playwright 의존성**: `page_fetcher.py` 이식 시 Playwright 패키지가 없을 경우 ImportError가 발생할 수 있다.
   `try/except ImportError`로 graceful 폴백 (requests 전용 모드) 처리한다.

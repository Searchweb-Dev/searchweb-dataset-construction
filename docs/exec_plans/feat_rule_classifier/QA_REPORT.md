# QA_REPORT: feat_rule_classifier

검수일: 2026-05-12
검수자: Evaluator Agent (claude-sonnet-4-6)
검수 대상 브랜치: feat/integrate-ai-url-classifier

---

## 1단계: 코드 구조 분석

### src/rule/ 구조 확인

```
src/rule/
├── __init__.py
├── analyzer.py          ← 신규 (RuleAnalyzer, _map_to_analysis_dict)
├── config.py            ← 이식 (EvalConfig, get_rule_config)
├── keywords.py          ← 이식
├── models.py            ← 이식 (EvaluationResult, CriterionResult 등)
├── pipeline.py          ← 신규 (run_quality_pipeline, DEFAULT_PIPELINE_STEPS)
├── utils.py             ← 이식
├── fetchers/
│   ├── __init__.py
│   └── page_fetcher.py  ← 이식
└── classifiers/
    ├── __init__.py
    ├── ai_scope_classifier.py
    ├── criteria_evaluator.py
    ├── discovery_signals.py
    ├── status_policy.py
    └── taxonomy_classifier.py
```

- `src/rule/`은 `ai_url_classifier/`를 임포트하지 않음 (grep 결과 참조 없음).
- `src/ai/analyzer.py`, `src/core/config.py`에 분기 로직 추가됨.
- `src/ai/detect.py`, `src/ai/analyze_task.py`는 이 브랜치에서 신규 생성된 파일임 (기존 존재 여부 기준으로 수정 제약 해석 불필요).
- `tests/rule/` 3개 파일 모두 존재.

---

## 2단계: SPEC 기능 검증

- [PASS] 기능 1: `src/rule/` 서브패키지 골격 생성
  - `python -c "from src.rule.pipeline import run_quality_pipeline"` 오류 없이 실행됨.
  - `python -c "from src.rule.models import EvaluationResult"` 오류 없이 실행됨.
  - `src/rule/` 전체에서 `ai_url_classifier` 참조 없음 (grep 결과 0건).
  - SPEC 명시 디렉터리 구조(`fetchers/`, `classifiers/`) 모두 완비.

- [PASS] 기능 2: `RuleAnalyzer` 클래스 구현
  - `src/rule/analyzer.py`에 `RuleAnalyzer` 클래스 구현됨.
  - `analyze_website(url: str) -> Dict[str, Any]` 메서드 존재.
  - 예외 전파 확인: `run_quality_pipeline` 예외 시 그대로 상위 전파 (흡수 없음).
  - 반환 dict에 `is_ai_tool`, `title`, `description`, `confidence`, `categories`, `tags`, `scores`, `analyzer` 포함.
  - `analyzer` 고정값 `"rule"`.
  - `title` 폴백: `homepage_title` → URL 호스트명 순서로 처리.

- [PASS] 기능 3: `_map_to_analysis_dict` 변환 함수
  - 순수 함수로 분리되어 독립 테스트 가능.
  - 6개 변환 규칙 모두 구현 확인:
    - `scope_decision="non_ai"` → `is_ai_tool=False` ✓
    - `scope_decision="uncertain"` → `is_ai_tool=True` ✓
    - `taxonomy_skipped=True` → `categories=[]` ✓
    - `total_score=50.0` → `scores.utility=5` ✓
    - `total_score=None` → `scores.utility=5` ✓
    - `has_privacy_or_data_policy.confidence=0.95` → `scores.trust=10` (round(9.5)=10) ✓
  - `scores.originality` 고정값 5 ✓
  - `confidence` 클램프 0.0–1.0 ✓

- [PASS] 기능 4: `get_analyzer()` 분기 확장
  - `src/ai/analyzer.py`에서 `get_classifier_mode()` 호출 후 `"rule"` 분기 처리됨.
  - `CLASSIFIER_MODE=rule` → `RuleAnalyzer()` 인스턴스 반환 확인.
  - `CLASSIFIER_MODE=llm` → 기존 LLM 분기 유지 확인.
  - `CLASSIFIER_MODE` 미설정 → 기존 LLM 분기 실행 확인.

- [PASS] 기능 5: `get_classifier_mode()` 헬퍼
  - `src/core/config.py`에 `get_classifier_mode() -> str` 추가됨.
  - 미설정 → `"llm"` ✓
  - `"rule"` → `"rule"` ✓
  - `"LLM"` → `"llm"` (소문자 정규화) ✓
  - `"invalid"` → `"llm"` + 경고 로그 ✓

- [PASS] 기능 6: 단위 테스트 작성
  - `tests/rule/test_map_to_analysis_dict.py` ✓
  - `tests/rule/test_get_classifier_mode.py` ✓
  - `tests/rule/test_get_analyzer_branching.py` ✓
  - 총 33개 테스트 전체 통과.

---

## 3단계: 정적 검사 + 테스트 실행 결과

### ruff check src/

```
Found 13 errors total:
- src/ai/_archive/_playwright_renderer.py: F401 unused import (Optional) ← 기존 파일
- src/api/deps.py: F401×2 unused imports ← 기존 파일
- src/api/routes.py: F401 unused import ← 기존 파일
- src/db/models/base.py: F401×2 unused imports ← 기존 파일

[src/rule/ 내 오류 - 이식된 코드 포함]
- src/rule/classifiers/status_policy.py:58: F841 할당 후 미사용 변수 `fetcher`
- src/rule/classifiers/taxonomy_classifier.py:9: F401 미사용 import `typing.Any`
- src/rule/pipeline.py:15-18: E402×4 logger 선언 후 모듈 수준 import (import 순서 위반)
- src/rule/pipeline.py:18: F401 미사용 import `DummyLLM`
```

신규 작성 파일(`src/rule/analyzer.py`, `src/ai/analyzer.py`, `src/core/config.py`)에서 ruff 오류 **0건**.  
이식된 파이프라인 코드(`src/rule/pipeline.py`, `src/rule/classifiers/`)에서 **7건** 발생.

### mypy src/ --ignore-missing-imports

```
src/rule/ 관련 오류 (이식된 코드): 37건
- CriteriaEvaluatorMixin/AiScopeClassifierMixin/StatusPolicyMixin/TaxonomyClassifierMixin이
  self.config 속성을 사용하지만 Mixin 클래스에 선언 없음 (실제로는 BaseToolQualityEvaluator가
  보유하지만 Mixin 단독으로 타입 해석 시 attr-defined 오류 발생)
- EvaluationResult.extracted가 Dict[str, object]로 선언돼 있어 내부 .get() 호출에 오류
- src/rule/fetchers/page_fetcher.py: PlaywrightTimeoutError 타입 어노테이션 오류 2건
- src/rule/classifiers/discovery_signals.py: seen_in_kind 타입 어노테이션 누락
```

신규 작성 파일(`src/rule/analyzer.py`, `src/ai/analyzer.py`, `src/core/config.py`)에서 mypy 오류 **0건**.  
이식된 코드에서 **37건** 발생 — 모두 Mixin 패턴의 `self.config` 미선언 및 `Dict[str, object]` 타입 표현력 부족 문제.

### pytest tests/rule/ -v

```
33 passed, 0 failed, 2 warnings (deprecation: FastAPI on_event)
0.16s
```

**전체 통과**.

---

## 4단계: 채점

### 1. 기능 정확성 (40%)
**8/10**

SPEC 기능 1–6 전체 구현되었고 테스트 33개 모두 통과한다. `_map_to_analysis_dict` 변환 규칙도 정확하게 구현됨. 감점 요인:
- `EvaluationResult.extracted` 필드가 `Dict[str, object]`로 선언되어 있어 `analyzer.py`에서 `.get()` 호출 시 런타임은 정상이나 mypy 오류 발생 가능성 내재. 실제로 mypy가 이 파일의 의존 경로(criteria_evaluator.py)에서 동일 문제를 잡아냄.
- `result.extracted`를 dict로 타입 캐스팅(`isinstance` 분기) 처리는 했으나, `EvaluationResult.extracted`가 `Dict[str, Any]`가 아닌 `Dict[str, object]`로 정의된 근본 문제가 해결되지 않음.

### 2. 코드 품질 (30%)
**6/10**

신규 작성 파일(`analyzer.py`, `ai/analyzer.py`, `config.py`)은 ruff 및 mypy 오류 0건, 타입 힌트 완비, 단일 책임 원칙 준수, docstring 완비.

이식된 코드에서 품질 문제:
- `src/rule/pipeline.py:15-18`: logger 선언 이후 import — E402 위반 (4건).
- `src/rule/pipeline.py:18`: `DummyLLM` 미사용 import (F401).
- `src/rule/classifiers/status_policy.py:58`: 할당 후 미사용 변수 `fetcher` (F841).
- `src/rule/classifiers/taxonomy_classifier.py:9`: `typing.Any` 미사용 import (F401).
- Mixin 클래스들이 `self.config`를 타입 선언 없이 사용 — mypy attr-defined 오류 37건.
- `EvaluationResult.extracted: Dict[str, object]` — `object`로 선언돼 내부 .get() 접근이 mypy에서 오류.

이식 시 기존 원본 코드의 품질 문제를 정리하지 않고 그대로 반입한 점이 감점 요인.

### 3. 성능 (15%)
**8/10**

- `_build_shared_text_cache`로 텍스트 블롭 캐시 공유 (ai_scope/taxonomy 중복 계산 방지) 적절.
- 병렬 fetch 설정 존재 (`parallel_candidate_fetch`, `candidate_fetch_workers`).
- `PageFetcher.close()` 호출로 리소스 정리 (`run_quality_pipeline` finally 블록).
- 성능상 명백한 문제는 없음. 감점 요인: `EvalConfig`에서 `lru_cache` 없이 반복 인스턴스화 가능 (소규모 영향).

### 4. 테스트 커버리지 (15%)
**8/10**

- 33개 테스트 전체 통과.
- 기능 3의 6개 케이스 모두 별도 독립 테스트로 존재 (`non_ai`, `uncertain`, `ai`, `taxonomy_skipped`, `total_score=50`, `total_score=None`).
- 기능 5의 4개 케이스 모두 존재 (미설정, `rule`, 대소문자, 잘못된 값).
- 기능 4의 분기 로직 별도 테스트 존재.
- AAA 패턴 일관되게 사용.
- 감점 요인:
  - `total_score=0` → `utility=1` (클램프) 케이스는 있으나 신뢰 점수 클램프(`confidence>1.0` 케이스) 엣지 케이스 없음.
  - `homepage_title`이 공백 문자열일 때 description 폴백 흐름 테스트 없음.
  - `_map_primary_category`의 매핑 미스 케이스(예: 빈 문자열) 별도 테스트 없음.

---

## 5단계: 최종 판정

**가중 점수 계산**:
- 기능 정확성 8/10 × 0.40 = 3.20
- 코드 품질 6/10 × 0.30 = 1.80
- 성능 8/10 × 0.15 = 1.20
- 테스트 커버리지 8/10 × 0.15 = 1.20

**가중 점수: 7.40 / 10.0**

---

```
**전체 판정**: 합격
**가중 점수**: 7.4 / 10.0

**항목별 점수**:
- 기능 정확성: 8/10 — SPEC 기능 1~6 전체 구현, 33개 테스트 전체 통과, EvaluationResult.extracted 타입 선언 불일치
- 코드 품질: 6/10 — 신규 파일 ruff/mypy 클린, 이식된 코드에서 ruff 7건/mypy 37건 미정리
- 성능: 8/10 — 캐시 공유·병렬 fetch·리소스 정리 적절, 명백한 비효율 없음
- 테스트 커버리지: 8/10 — 33개 전체 통과, 핵심 6+4+2 케이스 모두 존재, 일부 엣지 케이스 누락

**SPEC 기능 체크**:
- [PASS] 기능 1: src/rule/ 서브패키지 완비, ai_url_classifier 참조 없음, import 정상
- [PASS] 기능 2: RuleAnalyzer.analyze_website() 구현 및 예외 전파 확인
- [PASS] 기능 3: _map_to_analysis_dict 6개 변환 규칙 전체 구현
- [PASS] 기능 4: get_analyzer()에 CLASSIFIER_MODE 분기 추가, 상위 호출자 무수정
- [PASS] 기능 5: get_classifier_mode() 4가지 입력 케이스 모두 처리
- [PASS] 기능 6: tests/rule/ 3개 파일, 33개 테스트 전체 통과

**테스트 실행 결과**:
33 passed, 0 failed, 2 warnings (0.16s)
경고: FastAPI on_event 사용 deprecated 경고 — 기존 코드 문제, 이 작업과 무관

**구체적 개선 지시** (다음 이터레이션에서 수정 권장):

1. `src/rule/models.py:EvaluationResult.extracted` — `Dict[str, object]`를 `Dict[str, Any]`로 변경하라.
   `object` 타입은 mypy가 `.get()` 호출을 모두 오류로 잡아 criteria_evaluator.py에서 37건 오류를 유발한다.
   `from typing import Any`를 추가하고 `extracted: Dict[str, Any]`로 수정하면 mypy 오류 대부분 해소된다.

2. `src/rule/pipeline.py:13-18` — `logger = logging.getLogger(__name__)` 선언을 import 블록 아래로 이동하라.
   현재 구조는 E402 (module level import not at top of file) 4건을 유발한다.
   수정: 기존 `from __future__ import annotations` 및 `import logging` 다음에 바로 나머지 import를 배치하고, logger 선언은 마지막 import 이후로 옮긴다.

3. `src/rule/pipeline.py:18` — `DummyLLM` 미사용 import를 제거하라.
   `from src.rule.models import DummyLLM, EvaluationResult` → `from src.rule.models import EvaluationResult`.

4. `src/rule/classifiers/status_policy.py:58` — 미사용 변수 `fetcher` 할당을 제거하라.
   `fetcher = getattr(self, "fetcher", None)` 라인 삭제.

5. `src/rule/classifiers/taxonomy_classifier.py:9` — 미사용 `Any` import를 제거하라.
   `from typing import Any, Dict, List, Optional` → `from typing import Dict, List, Optional`.

6. `src/rule/classifiers/*.py` (AiScopeClassifierMixin, StatusPolicyMixin, TaxonomyClassifierMixin, CriteriaEvaluatorMixin) — `self.config` 접근에 대한 타입 힌트를 추가하라.
   각 Mixin 클래스 본문에 `config: EvalConfig` 클래스 변수 어노테이션을 추가한다 (예: `if TYPE_CHECKING: config: EvalConfig`).
   이를 통해 mypy attr-defined 오류 다수를 해소할 수 있다.

7. `src/rule/classifiers/discovery_signals.py:36` — `seen_in_kind` 변수에 타입 어노테이션을 추가하라.
   `seen_in_kind: Dict[str, set[str]] = {}` (또는 실제 타입에 맞게) 형태로 선언.

8. `tests/rule/test_map_to_analysis_dict.py` — 다음 엣지 케이스 테스트를 추가하라:
   - `homepage_title`이 공백 문자열일 때 description이 빈 문자열로 처리되는지 확인
   - `_map_primary_category`에서 매핑 테이블에 없는 값이 입력되면 `("other", "general")`을 반환하는지 확인

**방향 판단**: 현재 방향 유지
```

---

## 참고: 검증 명령 실행 기록

```
uv run python -c "from src.rule.pipeline import run_quality_pipeline" → OK
uv run python -c "from src.rule.models import EvaluationResult" → OK
uv run --with ruff ruff check src/rule/ → 7 errors (이식 코드, 신규 파일 0건)
uv run --with mypy mypy src/rule/ src/ai/analyzer.py src/core/config.py --ignore-missing-imports → 37 errors (이식 코드, 신규 파일 0건)
uv run python -m pytest tests/rule/ -v → 33 passed, 0 failed (0.16s)
```

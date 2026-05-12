# 자체 점검 — feat_rule_classifier

## SPEC 기능 체크

- [x] **기능 1: src/rule/ 서브패키지 골격 생성**
  - `src/rule/__init__.py`, `config.py`, `keywords.py`, `utils.py`, `models.py`, `pipeline.py` 생성
  - `src/rule/fetchers/__init__.py`, `page_fetcher.py` 생성
  - `src/rule/classifiers/__init__.py`, `ai_scope_classifier.py`, `criteria_evaluator.py`, `discovery_signals.py`, `status_policy.py`, `taxonomy_classifier.py` 생성
  - 모든 상대 임포트 → 절대 임포트(`from src.rule.*`) 변환 완료
  - `ai_url_classifier/` 참조 없음, `sys.path` 조작 없음
  - `python -c "from src.rule.pipeline import run_quality_pipeline"` 오류 없이 통과

- [x] **기능 2: RuleAnalyzer 클래스 구현**
  - `src/rule/analyzer.py`에 `RuleAnalyzer` 클래스 구현
  - `analyze_website(url: str) -> Dict[str, Any]` 메서드 공개
  - 내부에서 `run_quality_pipeline()` 호출 → `_map_to_analysis_dict()`로 변환
  - 예외를 흡수하지 않고 상위로 전파
  - 반환 dict에 필수 4개 필드(`is_ai_tool`, `title`, `description`, `confidence`) 포함
  - `analyzer` 값 고정 `"rule"`

- [x] **기능 3: _map_to_analysis_dict 순수 변환 함수 구현**
  - `src/rule/analyzer.py`에 `_map_to_analysis_dict(result, input_url)` 독립 함수 구현
  - 모든 세부 변환 규칙 구현:
    - `scope_decision` → `is_ai_tool` 매핑
    - `taxonomy_skipped=True` → `categories=[]`
    - `primary_category` → 카테고리 매핑 테이블(`_CATEGORY_MAP`) 변환
    - `total_score` → `scores.utility` (clamp 1–10, None 시 5)
    - `has_privacy_or_data_policy.confidence` → `scores.trust` (clamp 1–10, 키 없으면 5)
    - `scores.originality` 고정 5
    - `homepage_title` 없으면 URL 호스트명 폴백
    - `tags = sub_tasks[:3]`

- [x] **기능 4: get_analyzer() 분기 확장**
  - `src/ai/analyzer.py`의 `get_analyzer()`에 `CLASSIFIER_MODE` 분기 추가
  - `CLASSIFIER_MODE=rule` → `RuleAnalyzer()` 반환
  - 그 외 / 미설정 → 기존 LLM 분기 그대로 실행
  - `analyze_task.py`, `detector.py` 무수정 확인

- [x] **기능 5: get_classifier_mode() 환경변수 헬퍼 추가**
  - `src/core/config.py`에 `get_classifier_mode() -> str` 구현
  - 소문자 정규화 (`"LLM"` → `"llm"`, `"RULE"` → `"rule"`)
  - 미설정 시 `"llm"` 기본값 반환
  - 유효하지 않은 값(`llm`/`rule` 외) → 경고 로그 출력 후 `"llm"` 폴백

- [x] **기능 6: 단위 테스트 작성**
  - `tests/rule/__init__.py` 생성
  - `tests/rule/test_map_to_analysis_dict.py` — 기능 3 변환 규칙 18개 테스트
  - `tests/rule/test_get_classifier_mode.py` — 기능 5 환경변수 헬퍼 9개 테스트
  - `tests/rule/test_get_analyzer_branching.py` — 기능 4 분기 로직 6개 테스트
  - `pytest tests/rule/ -v` 전체 33개 테스트 PASSED (0 FAILED)
  - 외부 네트워크 호출 없음 (`run_quality_pipeline` mock 처리)

---

## 코드 자체 평가

### 금지 패턴 사용 여부

| 항목 | 결과 |
|------|------|
| `sys.path` 조작 | 없음 |
| `ai_url_classifier/` 임포트 | 없음 |
| `print()` 사용 (로깅 대신) | 없음 — 모두 `logging` 사용 |
| 하드코딩 API 키/시크릿 | 없음 |
| 예외 흡수 (`except: pass`) | 없음 |
| 상위 호출자(`analyze_task.py`, `detector.py`) 수정 | 없음 |

### 타입 힌트 적용률

| 파일 | 공개 함수/메서드 타입 힌트 |
|------|--------------------------|
| `src/rule/analyzer.py` | 100% (`_map_to_analysis_dict`, `RuleAnalyzer.analyze_website`) |
| `src/rule/pipeline.py` | 100% (`run_quality_pipeline`) |
| `src/rule/config.py` | 100% (dataclass 필드 + `get_rule_config`) |
| `src/rule/models.py` | 100% (dataclass 필드 전체) |
| `src/rule/utils.py` | 100% |
| `src/core/config.py` (추가분) | 100% (`get_classifier_mode`) |
| `src/ai/analyzer.py` (수정분) | 100% (기존 시그니처 유지) |

### 테스트 케이스 수

| 테스트 파일 | 케이스 수 | 커버 대상 |
|------------|-----------|---------|
| `test_map_to_analysis_dict.py` | 18 | `_map_to_analysis_dict` 변환 규칙 전체 |
| `test_get_classifier_mode.py` | 9 | `get_classifier_mode` 4개 입력 케이스 |
| `test_get_analyzer_branching.py` | 6 | `get_analyzer` 분기 + `RuleAnalyzer` 동작 |
| **합계** | **33** | — |

### 주요 설계 결정

1. **`run_quality_pipeline` 시그니처 변경**: 원본 `ai_url_classifier/pipeline.py`는 URL 리스트를 받아 리스트를 반환했으나, `RuleAnalyzer.analyze_website`의 단일 URL 인터페이스에 맞게 `url: str → EvaluationResult` 단일 반환으로 슬림화.

2. **Playwright graceful fallback**: `page_fetcher.py`에서 `try/except ImportError`로 Playwright 없는 환경에서도 requests 전용 모드로 동작. 의존성 설치 여부와 무관하게 패키지 임포트 자체는 성공.

3. **`_map_to_analysis_dict` 분리**: `RuleAnalyzer` 내에 내포하지 않고 모듈 레벨 순수 함수로 분리하여 독립 단위 테스트 가능.

4. **`_CATEGORY_MAP` + `_DEFAULT_CATEGORY`**: 8개 primary_category → (level_1, level_2) 매핑 테이블을 상수로 분리. 미매핑 시 `("other", "general")` 폴백.

5. **`beautifulsoup4` 의존성 추가**: `pyproject.toml`에 명시 추가 후 `uv sync` 실행. `ai_url_classifier/` 서브 venv에만 존재했던 패키지를 프로젝트 루트 venv에 통합.

6. **`[tool.pytest.ini_options] pythonpath = ["."]`**: `src/` 절대 임포트가 pytest 실행 컨텍스트에서도 동작하도록 프로젝트 루트를 `PYTHONPATH`에 포함.

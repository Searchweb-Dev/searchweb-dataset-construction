# AI URL Classifier (v1.1.3)

AI 툴/서비스 후보 URL을 입력으로 받아, 공개 웹페이지에서 확인 가능한 신호만으로 해당 사이트가 실제 AI 서비스인지 판정하고, taxonomy와 품질 상태를 평가해 JSON 파일로 저장하는 로컬 CLI 파이프라인이다.

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
- tool registry 스냅샷(`management`) 생성
- tool별 변경 이력(`result/tool_registry.json`) 누적
- 핵심 규칙 단위 테스트

현재 구현 범위 밖:

- Postgres 적재
- ORM/세션 연결
- insert/upsert
- 자동 스케줄링
- 실제 외부 LLM 연동

관련 문서:

- [ARCHITECTURE.md](./ARCHITECTURE.md) — 파이프라인 구조, 모듈 설계, 상태 모델
- [research.md](./research.md) — 상세 코드 분석

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
python run.py --output-json ./outputs/result.json https://chatgpt.com
python run.py --source ai-tools.json --registry-json result/tool_registry.json --url-file data/site_url_list.txt
```

### 1.3 테스트 실행

```bash
python -m unittest discover -s tests -p "test_*.py"
```

입력 규칙:

- 여러 URL을 공백으로 나열해 한 번에 실행할 수 있다.
- `.txt` 파일 경로를 직접 넘기면 줄 단위 URL 목록으로 읽는다.
- `--url-file <path>`도 지원한다.
- `--output-json <path>`로 결과 JSON 저장 경로를 지정할 수 있다.
- `--source <label>`로 수집/실행 출처 라벨을 결과에 기록할 수 있다.
- `--registry-json <path>`로 도구 레지스트리 파일 위치를 지정할 수 있다.
- `--registry-json none`으로 레지스트리 저장을 비활성화할 수 있다.
- 쿼리스트링이 포함된 URL은 반드시 따옴표로 감싸야 한다.
- 셸에서 `&`는 백그라운드 실행 기호로 해석되므로 URL이 잘릴 수 있다.

## 2. 출력 형태

결과는 JSON 파일로 저장된다.

기본 저장 위치:

- `ai_url_classifier/result/results_YYYYMMDD_HHMMSS.json`
- `ai_url_classifier/result/tool_registry.json`

경로를 직접 지정하려면:

- `python run.py --output-json ./outputs/result.json --url-file data/site_url_list.txt`

각 항목에는 아래 정보가 포함된다.

- 입력 URL과 정규화 URL
- `predicted_status`, `final_status`
- `passed_count`, `hard_pass`
- `review_required`, `review_reasons`
- 5개 criterion 상세
- `summary`
- `extracted`
- `total_score`, `score_breakdown`
- `management` (tool_id, canonical_url, aliases, lifecycle_state, review_queue_reasons 등)

`tool_registry.json`은 도구별 최신 스냅샷과 change history를 누적 저장한다. `first_seen_at/last_checked_at`, 상태 변화, taxonomy/score/review 변화 추적에 사용할 수 있다.

## 3. 향후 확장

- Postgres 적재 및 insert/upsert
- change log 저장
- 재검증 스케줄러
- 대표 사이트셋 기반 회귀 테스트
- 실제 LLM 연동

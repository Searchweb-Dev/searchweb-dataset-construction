# Threads URL Extraction MVP

Threads 키워드 검색 결과에서 게시글 본문 URL을 추출하고, 도메인/서비스명 빈도를 집계하는 Python MVP입니다.  
기본 실행 모드는 `MockThreadsClient`이며, 실제 API 연동은 환경변수로 전환합니다.

## 1) 설치 방법
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) 환경변수 설정 방법
```bash
cp .env.example .env
```

주요 설정:
- `DATABASE_URL`
- `THREADS_USE_MOCK=true|false`
- `THREADS_API_TOKEN` (실제 API 모드일 때 필수)
- `THREADS_SEARCH_PATH` (기본값: `/v1.0/keyword_search`)
- `THREADS_SEARCH_TYPE` (기본값: `TOP`)
- `THREADS_SEARCH_MODE` (기본값: `KEYWORD`)
- `THREADS_FIELDS` (기본값: 문서 예시 기준 Threads 게시물 필드)
- `DEFAULT_KEYWORDS_CSV`

## 3) DB 마이그레이션 방법
```bash
alembic upgrade head
```

## 4) mock 모드 실행 방법
`.env`에서 아래 값을 사용:
```env
THREADS_USE_MOCK=true
```

실행:
```bash
python -m app.cli run-all --keywords "AI 툴,AI 서비스"
```

## 5) CLI 사용 예시
수집:
```bash
python -m app.cli collect --keywords "AI 서비스,AI 툴,AI 추천"
```

URL 추출:
```bash
python -m app.cli extract-urls
```

서비스명 추출:
```bash
python -m app.cli extract-tools --only-without-urls
```

집계:
```bash
python -m app.cli aggregate --top-n 10
```

전체 파이프라인:
```bash
python -m app.cli run-all --keywords "AI 툴,AI 서비스"
```

## 6) 현재 한계
- 실제 Threads API 응답 스키마가 변하면 `app/parsers/threads_parser.py`의 필드 매핑 수정이 필요합니다.
- short URL 확장은 인터페이스만 제공하며 기본 구현은 no-op입니다.
- 서브도메인의 registered-domain 판별은 간단 규칙 기반입니다.
- `posts.keyword`는 동일 게시글이 여러 키워드로 수집될 때 마지막 키워드로 갱신됩니다.

## 7) 실제 Threads API 연결 시 수정이 필요한 지점
- `app/clients/threads_api.py`
  - `search_path`, 요청 파라미터(`q`, `search_type`, `search_mode`, `fields`, `access_token`)를 최신 공식 문서에 맞춰 검증
  - 필요 시 `media_type`, `since`, `until` 파라미터 추가
- `app/parsers/threads_parser.py`
  - 실제 응답에서 `platform_post_id`, `content`, `author_handle` 경로 확정 후 매핑 업데이트
- `app/config.py`
  - 운영 환경 키/타임아웃/리밋 튜닝

## 프로젝트 구조
```text
project_root/
  app/
    __init__.py
    cli.py
    config.py
    db.py
    logging.py
    models/
      __init__.py
      post.py
      url.py
      tool.py
    schemas/
      __init__.py
      threads.py
    clients/
      __init__.py
      base.py
      threads_api.py
      threads_mock.py
    services/
      __init__.py
      collector.py
      url_extractor.py
      domain_normalizer.py
      tool_extractor.py
      aggregator.py
    repositories/
      __init__.py
      posts.py
      urls.py
      tools.py
    parsers/
      __init__.py
      threads_parser.py
  tests/
    test_url_extractor.py
    test_domain_normalizer.py
    test_threads_parser.py
    test_aggregator.py
  alembic/
  alembic.ini
  .env.example
  requirements.txt
  README.md
```

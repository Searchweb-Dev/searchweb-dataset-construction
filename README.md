# sw_test

두 개 프로젝트의 통합 작업 디렉터리.

## 디렉터리 구성

- `ai_url_classifier/`
  - AI 툴/서비스 URL 평가 및 분류 파이프라인.
  - `run.py` 단일 엔트리포인트, `src/` 구현 모듈 구조.
  - 상세 문서: [ai_url_classifier/README.md](/mnt/c/Users/kang/Desktop/sw_test/ai_url_classifier/README.md)

- `url_ingest/`
  - Threads 기반 URL 수집/추출 리서치 및 수집 MVP.
  - 리서치 문서 + `threads_url_pipeline/` 구현 프로젝트 구성.
  - 리서치 문서: [url_ingest/threads_url_pipeline/threads_url_extraction_research.md](/mnt/c/Users/kang/Desktop/sw_test/url_ingest/threads_url_pipeline/threads_url_extraction_research.md)
  - 구현 문서: [url_ingest/threads_url_pipeline/README.md](/mnt/c/Users/kang/Desktop/sw_test/url_ingest/threads_url_pipeline/README.md)

## 작업 위치

- AI 툴/서비스 분류 작업: `ai_url_classifier/`
- Threads URL 수집/추출 작업: `url_ingest/threads_url_pipeline/`

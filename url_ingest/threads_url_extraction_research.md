# Threads URL 추출 가능성 검토 (API 우선 설계)
작성일: 2026-04-06 (KST)

## 1. 결론
- **가능 여부:** 목표(키워드 기반 게시글 수집 + 게시글 내 웹사이트 URL 추출)는 **공식 Threads API 중심으로 가능**합니다. [출처: 공식1, 공식2, 공식3]
- **우선 전략:** **API 우선**이 맞고, 크롤링은 메인 전략으로 권장하지 않습니다. [출처: 공식6, 공식7]

이유(핵심 5개):
1. Threads는 `GET /keyword_search`로 키워드/주제태그 검색을 공식 지원합니다. [출처: 공식1, 공식5]
2. 검색 결과에서 `text`, `permalink`를 요청할 수 있고, 미디어 필드로 `link_attachment_url`도 공식 필드로 제공됩니다. [출처: 공식1, 공식2, 공식3]
3. 권한 승인 전/후의 검색 범위 제약이 문서에 명시되어 있어 운영 정책이 예측 가능합니다. [출처: 공식1]
4. Threads `robots.txt`는 자동 수집 금지(서면 허가 필요)와 `User-agent: * / Disallow: /`를 명시합니다. [출처: 공식6]
5. Meta Automated Data Collection Terms는 명시적 서면 허가 없는 자동 수집 금지와 집행/권한 철회 가능성을 명시합니다. [출처: 공식7]

## 2. 근거 조사
### 2-1. 공식 문서 기준 확인된 사실
- Threads 키워드 검색 엔드포인트(`GET /keyword_search`)가 존재하며, `q`, `search_type`, `search_mode`, `media_type`, `since`, `until`, `limit`, `author_username` 등을 사용합니다. [출처: 공식1]
- 키워드 검색에는 `threads_basic` + `threads_keyword_search` 권한이 필요합니다. [출처: 공식1]
- `threads_keyword_search` 미승인 상태에서는 인증 사용자 소유 게시물 중심으로 제한되고, 승인 후 공개 게시물 검색이 가능하다고 명시됩니다. [출처: 공식1]
- 검색 결과 필드로 `text`, `permalink`를 요청할 수 있습니다. [출처: 공식1]
- 미디어 필드에 `link_attachment_url`(게시물 첨부 URL)이 존재합니다. [출처: 공식2, 공식3]
- 키워드 검색 제한은 사용자 기준 24시간 2,200쿼리로 명시됩니다. [출처: 공식1]
- Threads changelog에서 키워드 검색(2024-12-09), 검색 제한 변경(2025-06-25), 주제태그/시간필터(2025-07-14), media_type 검색(2025-09-09), author_username 필터(2026-01-20) 추가 이력이 확인됩니다. [출처: 공식5]
- Threads robots.txt에 자동 수집 금지 고지와 `User-agent: *`에 대한 전면 `Disallow: /`가 있습니다. [출처: 공식6]
- Automated Data Collection Terms는 서면 허가 없는 자동 수집 금지, robots/opt-out 준수, 집행/감사/권한 철회를 명시합니다. [출처: 공식7]

### 2-2. 아직 확정되지 않은 부분
- `text` 필드가 항상 “원문 전체”인지(길이 제한/절단 여부)는 문서에서 명시적으로 확인하지 못했습니다. [출처: 공식1, 공식2]
- `text_entities`가 URL 엔티티를 구조적으로 제공하는지 여부는 문서 설명만으로 확정되지 않습니다(문서에는 스포일러 관련 설명이 중심). [출처: 공식2, 공식3]
- 검색 결과의 랭킹 로직/회수율(coverage) 세부 기준은 공개 문서에서 확인하지 못했습니다. [출처: 공식1]

### 2-3. 추가 검증이 필요한 부분
- 실제 앱 권한 승인 상태에서 공개 게시물 회수율(키워드별 hit-rate) 검증이 필요합니다. [출처: 공식1]
- `fields=text,link_attachment_url` 요청 시 URL 추출 재현율(정답 대비)을 샘플 기반으로 검증해야 합니다. [출처: 공식1, 공식2, 공식3]
- 쿼리 한도(2,200/24h) 내에서 운영 주기별 수집량이 목표를 만족하는지 부하 테스트가 필요합니다. [출처: 공식1]

## 3. API 방식 검토
### 3-1. 가능한 작업
- 키워드/태그 기반 게시글 검색: `GET /keyword_search`. [출처: 공식1]
- 검색 조건 제어: TOP/RECENT, KEYWORD/TAG, TEXT/IMAGE/VIDEO, 기간 필터, 작성자 필터. [출처: 공식1, 공식5]
- 본문/링크 추출 기반 필드 수집: `text`, `permalink`, `link_attachment_url` 등. [출처: 공식1, 공식2, 공식3]

### 3-2. 필요한 권한/조건
- OAuth 인증 플로우로 사용자 액세스 토큰 발급이 필요합니다. [출처: 공식4]
- 필수 권한: `threads_basic`, 키워드 검색에는 `threads_keyword_search`. [출처: 공식1, 공식4]
- `threads_keyword_search` 승인 상태에 따라 검색 대상 범위가 달라집니다. [출처: 공식1]

### 3-3. 예상 한계
- 사용자당 24시간 2,200쿼리 제한이 있어 키워드 조합이 많으면 샘플링 전략이 필요합니다. [출처: 공식1]
- URL이 본문 텍스트로만 존재하고 `link_attachment_url`가 비어있는 경우, 텍스트 파싱 정확도에 의존합니다. [출처: 공식1, 공식2, 공식3]
- URL이 없고 툴명만 언급된 게시글은 별도 서비스명 추출 로직이 필요합니다. [추론]

### 3-4. URL 추출 관점 장단점
- 장점: 공식 필드(`text`, `link_attachment_url`) 기반이라 수집 경로가 안정적입니다. [출처: 공식1, 공식2, 공식3]
- 장점: 정책/권한 체계가 문서화되어 장기 운영 리스크 관리가 가능합니다. [출처: 공식1, 공식4, 공식5]
- 단점: 쿼리 한도와 승인 범위 조건에 영향을 받습니다. [출처: 공식1]

## 4. 크롤링 방식 검토
### 4-1. 기술적으로 가능한 범위
- 공개 웹 페이지 HTML 응답은 수신 가능하지만, 루트 페이지가 로그인 유도(`Threads • Log in`)와 대량 스크립트 로딩 구조를 보입니다. [출처: 공식8]
- 따라서 단순 정적 HTML 파싱만으로 안정 수집하기 어렵고 렌더링/세션 처리 복잡도가 높습니다. [출처: 공식8, 추론]

### 4-2. 예상 구현 방식
- (기술 관점) URL 패턴 페이지를 순회하며 HTML 파싱 + 동적 렌더링 보완(헤드리스 브라우저) 방식이 필요할 가능성이 큽니다. [출처: 공식8, 추론]
- 그러나 이 방식은 정책/약관 리스크가 커서 본 프로젝트의 메인 전략으로 부적합합니다. [출처: 공식6, 공식7]

### 4-3. 차단/로그인/동적 렌더링 리스크
- `robots.txt`가 전면 `Disallow`를 선언하고 자동 수집 금지 고지를 명시해 차단/분쟁 리스크가 높습니다. [출처: 공식6]
- 약관상 집행(권한 철회/중단 요구/삭제 요구) 가능성이 명시되어 운영 지속성이 낮습니다. [출처: 공식7]
- 로그인/동적 렌더링 구조로 인해 DOM 변경 대응 비용이 큽니다. [출처: 공식8, 추론]

### 4-4. robots.txt 및 정책 리스크
- Threads robots 고지: 서면 허가 없는 자동 수집 금지. [출처: 공식6]
- Meta 약관: 별도 공식 승인 없는 자동 수집 금지, robots/opt-out 준수 의무. [출처: 공식7]

### 4-5. 운영 적합성 평가
- 장기 운영 적합성은 낮습니다(정책 리스크가 기술 이점보다 큼). [출처: 공식6, 공식7, 추론]

## 5. 비교표
| 항목 | Threads API | 크롤링 | 평가 |
|---|---|---|---|
| 검색 가능 여부 | `GET /keyword_search`로 공식 지원 [공식1] | 기술적으로 페이지 순회는 가능하나 정책 제약 큼 [공식6, 공식7] | API 우위 |
| 게시글 본문 확보 가능 여부 | `text` 필드 요청 가능 [공식1, 공식2] | 페이지 구조/로그인/동적 렌더링 영향 큼 [공식8] | API 우위 |
| URL 추출 가능성 | `link_attachment_url` + `text` 파싱 병행 가능 [공식1, 공식2, 공식3] | HTML 파싱 가능하지만 안정성 낮음 [공식8] | API 우위 |
| 안정성 | 공식 엔드포인트/권한 체계 존재 [공식1, 공식4, 공식5] | 프론트 구조 변경에 취약 [공식8, 추론] | API 우위 |
| 유지보수성 | 버전/권한 기준으로 관리 가능 [공식1, 공식5] | 셀렉터/렌더링 의존 유지보수 비용 큼 [공식8, 추론] | API 우위 |
| 정책/약관/robots 리스크 | 낮음(공식 절차 준수 시) [공식1, 공식4] | 매우 높음(`Disallow: /`, 서면허가 요구) [공식6, 공식7] | API 압도적 우위 |
| 장기 운영 적합성 | 높음(승인/쿼터 설계 전제) [공식1, 공식5] | 낮음(집행 리스크 상시) [공식6, 공식7] | API 우위 |

## 6. 최종 권장 아키텍처
요청하신 흐름 기준 설계:

1. **키워드 검색**  
`GET /keyword_search`로 키워드/태그를 수집하고 `search_type=RECENT` 중심으로 주기 실행합니다. [출처: 공식1]

2. **게시글 저장**  
원본 응답(`id`, `text`, `permalink`, `timestamp`, `username`, `media_type`, `link_attachment_url`)을 원문(JSON)과 함께 저장합니다. [출처: 공식1, 공식2, 공식3]

3. **본문 URL 추출**  
1차: `link_attachment_url` 사용, 2차: `text`에서 URL 정규식 추출을 병행합니다. [출처: 공식1, 공식2, 공식3, 추론]

4. **도메인 정규화**  
호스트 소문자화, `www.` 제거, 추적 파라미터 제거 후 `domain`/`registered_domain` 단위로 집계합니다. [추론]

5. **URL 없는 게시글의 서비스명 추출**  
`text`에서 서비스명 후보를 추출하고(사전 + 패턴), URL 기반 도메인 사전과 매칭해 보조 집계합니다. [출처: 공식1, 추론]

6. **빈도 집계**  
`normalized_domain` 기준 빈도, 고유 게시글 수, 고유 작성자 수를 산출합니다. [추론]

7. **중복 제거**  
`post_id`/`permalink` 기준 중복 제거, 동일 게시글 내 중복 URL 제거를 수행합니다. [출처: 공식1, 추론]

8. **품질 보정**  
단축 URL 해제(선택), 스팸성 도메인 필터, 비영어/한글 혼용 키워드 정제를 적용합니다. [추론]

## 7. MVP 설계
### 7-1. 저장 데이터 스키마(최소)
- `posts`  
`post_id`(PK), `query`, `search_mode`, `search_type`, `media_type`, `username`, `text`, `link_attachment_url`, `permalink`, `posted_at`, `fetched_at`, `raw_json` [출처: 공식1, 공식2, 공식3]
- `post_urls`  
`post_id`, `url_raw`, `url_source`(`link_attachment_url`/`text_regex`), `url_normalized`, `domain`, `registered_domain` [추론]
- `post_service_mentions`  
`post_id`, `service_name`, `confidence`, `method`(`dictionary`/`pattern`) [추론]

### 7-2. 수집 주기
- 기본: 30분 주기 + 키워드 세트 분할 실행(쿼터 보호). [출처: 공식1, 추론]
- 계산 기준: 사용자당 24시간 2,200쿼리 한도를 초과하지 않도록 키워드 수 × 주기를 제어합니다. [출처: 공식1]

### 7-3. URL 추출 규칙
- 규칙 1: `link_attachment_url`가 있으면 우선 채택. [출처: 공식3]
- 규칙 2: `text`에서 `https?://` 및 `www.` 패턴 추출. [출처: 공식1, 추론]
- 규칙 3: 괄호/문장부호 후행 문자 제거, 중복 URL 제거. [추론]

### 7-4. 도메인 정규화 규칙
- `scheme`/`www` 정리, host lowercase, 포트 제거. [추론]
- 집계용 canonical에서는 `utm_*`, `fbclid` 등 추적 파라미터 제거. [추론]

### 7-5. 서비스명 보조 추출 규칙
- URL 없는 게시글만 대상으로 `text`에서 서비스 후보를 추출합니다. [출처: 공식1, 추론]
- 사전 기반(상위 도메인→서비스명 맵) + 패턴 기반(대문자/브랜드 토큰) 병행. [추론]
- 신뢰도 낮은 항목은 “후보”로만 저장하고 메인 집계와 분리합니다. [추론]

### 7-6. 집계 지표
- `domain_share_count`(도메인 공유 횟수)
- `domain_unique_posts`
- `domain_unique_authors`
- `service_mention_count_without_url`
- `url_attachment_ratio`(`link_attachment_url` 존재 비율) [출처: 공식3, 추론]

## 8. 권장안
### 지금 바로 시작할 방식
- **공식 API 기반 MVP**로 시작합니다: `keyword_search` + `text/link_attachment_url` 추출 + 도메인 집계. [출처: 공식1, 공식2, 공식3]
- 권한 승인 상태를 먼저 확인하고, 승인 전에는 제한 범위 데이터로 파이프라인 검증만 수행합니다. [출처: 공식1]

### 하지 말아야 할 방식
- **robots/약관을 우회하는 웹 크롤링을 메인 수집 전략으로 채택하지 마세요.** [출처: 공식6, 공식7]

그 이유:
1. robots에서 자동 수집 금지 및 전면 Disallow를 명시합니다. [출처: 공식6]
2. 약관에서 서면 허가 없는 자동 수집 금지와 집행 조치를 명시합니다. [출처: 공식7]
3. 장기 운영 관점에서 정책 리스크가 기술 리스크보다 치명적입니다. [출처: 공식6, 공식7, 추론]

## 9. 불확실성
- `text_entities`의 URL 엔티티 활용 가능성은 문서만으로 확정 불가입니다. [출처: 공식2, 공식3]
- 키워드별 실제 회수율/중복률/노이즈율은 실측 전 확정 불가입니다. [출처: 공식1, 추론]
- 서비스명 추출 품질(특히 URL 없는 게시글)은 사전 품질에 크게 좌우되므로 PoC 실험이 필요합니다. [추론]

추가 실험/확인 제안:
1. 권한 승인 전/후 동일 키워드 결과량 비교 실험. [출처: 공식1]
2. `link_attachment_url` 존재율 vs `text` 정규식 추출율 비교.
3. URL 없는 게시글의 서비스명 추출 정밀도/재현율 샘플 평가.
4. 30분 주기 운용 시 쿼리 한도 여유율 모니터링.
5. 도메인 정규화 전/후 순위 변동(노이즈 감소 효과) 검증.

---

## 출처 구분
### 공식 문서/정책
- 로컬 스냅샷(`url_ingest/raw/*`)은 2026-04-07 정리 작업으로 삭제되었습니다. 아래 URL을 기준으로 재확인할 수 있습니다.
- **공식1**: Meta for Developers, Threads Keyword Search  
  URL: https://developers.facebook.com/docs/threads/keyword-search  
- **공식2**: Meta for Developers, Threads Media Retrieval/Discovery  
  URL: https://developers.facebook.com/docs/threads/retrieve-and-discover-posts/retrieve-posts  
- **공식3**: Meta for Developers, Threads Media Fields  
  URL: https://developers.facebook.com/docs/threads/threads-media  
- **공식4**: Meta for Developers, Get Access Tokens  
  URL: https://developers.facebook.com/docs/threads/get-started/get-access-tokens-and-permissions  
- **공식5**: Meta for Developers, Threads Changelog  
  URL: https://developers.facebook.com/docs/threads/changelog  
- **공식6**: Threads robots.txt  
  URL: https://www.threads.com/robots.txt  
- **공식7**: Meta Automated Data Collection Terms  
  URL: https://www.facebook.com/legal/automated_data_collection_terms  
- **공식8**: Threads Web Root Response (`https://www.threads.com/`)  
  근거 포인트: 로그인 유도 메타, 다수 스크립트 로딩 확인

### 비공식 자료
- 본 문서에서는 비공식 블로그/커뮤니티 자료를 근거로 사용하지 않았습니다.

---

## 바로 실행 가능한 다음 행동 5개
- [ ] Meta 앱에서 `threads_basic`, `threads_keyword_search` 권한 상태와 승인 범위를 확인한다. [출처: 공식1, 공식4]
- [ ] 키워드 세트(예: `AI 서비스`, `AI 툴`, `AI 추천`, 영문 동의어 포함)를 확정하고 30분 주기 쿼리 예산표를 만든다. [출처: 공식1]
- [ ] `fields=text,link_attachment_url,permalink,timestamp,username` 기준으로 API 샘플 1주치 수집을 시작한다. [출처: 공식1, 공식2, 공식3]
- [ ] URL 정규화/도메인 집계 규칙을 고정하고, 전/후 지표를 비교해 규칙을 잠근다.
- [ ] URL 없는 게시글에 대한 서비스명 보조 추출을 별도 파이프라인으로 분리해 정확도 검증 후 병합 여부를 결정한다.

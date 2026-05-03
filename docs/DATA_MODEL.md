# SearchWeb 데이터 모델 (v0.3.0)

북마크/링크/폴더 관리 서비스를 위한 전체 데이터 정의 문서.

---

## 핵심 도메인 구조

| 도메인 | 설명 | 테이블 수 | 테이블명 |
|--------|------|----------|---------|
| **base** | 모든 엔티티 공통 컬럼 | 1 | `base_entity` |
| **auth** | 사용자 인증 | 2 | `member`, `oauth_member` |
| **taxonomy** | 카테고리 분류 | 1 | `category_master` |
| **member** | 개인 폴더/저장/태그 | 5 | `member_folder`, `member_saved_link`, `member_tag`, `member_saved_link_tag`, `member_folder_tag` |
| **link** | 링크 메타데이터 | 1 | `link` |
| **enrichment** | 자동 채우기/추천/피드백 | 4 | `folder_suggestion_rule`, `link_enrichment`, `link_enrichment_keyword`, `link_enrichment_feedback` |
| **team** | 팀 협업(v0.4.0) | 7 | `team`, `team_member`, `team_folder`, `team_folder_permission`, `team_saved_link`, `team_tag`, `team_saved_link_tag` |

**현재 v0.3.0: 14개 테이블 (개인 도메인 완성)**

---

## 테이블 정의

### base_entity (공통 템플릿/믹스인)

실제 DB 물리 테이블이 아닌 모든 엔티티에 공통으로 적용되는 "컬럼 규약/템플릿".

| 컬럼명 | 타입 | NULL | 기본값 | 설명 |
|--------|------|------|--------|------|
| `created_at` | timestamptz | not null | now() | 생성 시각 |
| `updated_at` | timestamptz | not null | now() | 마지막 수정 시각(UPDATE 시 갱신) |
| `deleted_at` | timestamptz | - | - | 소프트 삭제 시각(NULL이면 미삭제) |
| `created_by_member_id` | bigint | - | - | 생성자 사용자 ID(논리 참조) |
| `updated_by_member_id` | bigint | - | - | 수정자 사용자 ID(논리 참조) |
| `deleted_by_member_id` | bigint | - | - | 삭제자 사용자 ID(논리 참조) |

---

### member (auth 스키마)

서비스 사용자 계정 기본 정보. 팀/폴더/링크 저장 등 대부분 기능에서 참조되는 최상위 엔티티.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `member_id` | bigint | not null | identity | PK | - |
| `email` | varchar(255) | not null | - | uq_member_email | - |
| `login_id` | varchar(50) | - | - | uq_member_login_id | - |
| `password_hash` | varchar(255) | - | - | - | - |
| `member_name` | varchar(20) | not null | - | - | - |
| `job` | varchar(20) | - | - | - | - |
| `major` | varchar(20) | - | - | - | - |
| `status` | varchar(20) | not null | 'active' | - | idx_member_status |
| + base_entity | | | | | |

**제약조건:**
- `ck_member_login_pw_pair`: (login_id IS NULL AND password_hash IS NULL) OR (login_id IS NOT NULL AND password_hash IS NOT NULL)
- `ck_member_status`: status IN ('active','blocked')

---

### oauth_member (auth 스키마)

소셜 로그인(제공자/제공자 사용자키)과 내부 사용자 계정을 매핑한다.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `oauth_member_id` | int | not null | identity | PK | - |
| `member_id` | bigint | not null | - | - | idx_oauth_member_member_id |
| `provider` | varchar(30) | not null | - | - | idx_oauth_member_provider |
| `provider_member_key` | varchar(255) | not null | - | uq_oauth_member(provider, provider_member_key) | - |
| + base_entity | | | | | |

---

### category_master (taxonomy 스키마)

링크 자동 분류에 사용하는 카테고리 마스터. 현재는 대분류만 운영하되, 확장 대비 트리 구조 지원.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `category_id` | int | not null | identity | PK | - |
| `parent_category_id` | int | - | - | - | idx_category_parent |
| `category_name` | varchar(80) | not null | - | uq_category_name(조건부) | idx_category_name |
| `category_level` | smallint | not null | 1 | - | idx_category_level |
| `is_active` | boolean | not null | true | - | idx_category_active |
| + base_entity | | | | | |

**제약조건:**
- `ck_category_level`: category_level IN (1,2)

---

### member_folder (member 스키마)

개인 사용자가 소유하는 폴더. parent_folder_id로 최대 2층 구조를 지원한다.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `member_folder_id` | int | not null | identity | PK | - |
| `owner_member_id` | bigint | not null | - | - | idx_member_folder_owner |
| `parent_folder_id` | int | - | - | - | idx_member_folder_parent |
| `folder_name` | varchar(80) | not null | - | uq_member_folder(owner,parent,name) | idx_member_folder_name |
| `description` | text | - | - | - | - |
| + base_entity | | | | | |

**외래키:**
- `owner_member_id` → `member.member_id`
- `parent_folder_id` → `member_folder.member_folder_id`

---

### member_saved_link (member 스키마)

사용자가 개인 폴더에 링크를 저장한 항목. 대표 카테고리(시스템/사용자 보정)를 포함해 필터링/정렬이 가능.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `member_saved_link_id` | int | not null | identity | PK | - |
| `link_id` | bigint | not null | - | uq_member_saved_link(folder,link) | idx_member_saved_link_link |
| `link_enrichment_id` | int | - | - | - | idx_member_saved_link_enrichment |
| `member_folder_id` | int | not null | - | - | idx_member_saved_link_folder |
| `display_title` | varchar(255) | not null | - | - | idx_member_saved_link_title |
| `note` | text | - | - | - | - |
| `primary_category_id` | int | - | - | - | idx_member_saved_link_primary_category |
| `category_source` | varchar(10) | not null | 'system' | - | - |
| `category_score` | numeric(5,4) | - | - | - | - |
| + base_entity | | | | | |

**제약조건:**
- `ck_member_saved_link_category_source`: category_source IN ('system','member')
- `ck_member_saved_link_category_score`: category_score IS NULL OR (category_score BETWEEN 0 AND 1)

---

### member_tag (member 스키마)

사용자가 직접 만드는 개인 태그(단어) 마스터. 개인 저장 항목에 부착하여 검색/필터에 사용.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `member_tag_id` | bigint | not null | identity | PK | - |
| `owner_member_id` | bigint | not null | - | uq_member_tag(owner,name) | idx_member_tag_owner |
| `tag_name` | varchar(50) | not null | - | - | - |
| + base_entity | | | | | |

---

### member_saved_link_tag (member 스키마 - 매핑 테이블)

저장 항목(개인)에 개인 태그(member_tag)를 부착한다. 검색/필터에 사용.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `member_saved_link_tag_id` | bigint | not null | identity | PK | - |
| `member_saved_link_id` | bigint | not null | - | uq_member_saved_link_tag(link,tag) | idx_member_saved_link_tag_item |
| `member_tag_id` | bigint | not null | - | - | idx_member_saved_link_tag_tag |
| `created_at` | timestamptz | not null | now() | - | - |

---

### member_folder_tag (member 스키마 - 매핑 테이블)

개인 폴더에 개인 태그(member_tag)를 부착한다.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `member_folder_tag_id` | bigint | not null | identity | PK | - |
| `member_folder_id` | int | not null | - | uq_member_folder_tag(folder,tag) | idx_member_folder_tag_item |
| `member_tag_id` | bigint | not null | - | - | idx_member_folder_tag_tag |
| `created_at` | timestamptz | not null | now() | - | - |

---

### link (link 스키마)

URL 대상(정규화 URL, 메타 정보, 자동분류 대표 카테고리/점수/버전/시각)을 저장한다. 동일 URL은 1건으로 재사용.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `link_id` | bigint | not null | identity | PK | - |
| `canonical_url` | text | not null | - | uq_link_canonical | - |
| `original_url` | text | not null | - | - | - |
| `domain` | varchar(255) | - | - | - | idx_link_domain |
| `title` | varchar(255) | - | - | - | idx_link_title |
| `description` | text | - | - | - | - |
| `thumbnail_url` | text | - | - | - | - |
| `favicon_url` | text | - | - | - | - |
| `content_type` | varchar(30) | not null | 'link' | - | idx_link_content_type |
| `primary_category_id` | int | not null | - | - | idx_link_primary_category |
| `category_score` | numeric(5,4) | - | - | - | - |
| `classifier_version` | varchar(50) | - | - | - | - |
| `categorized_at` | timestamptz | - | - | - | idx_link_categorized_at |
| + base_entity | | | | | |

**제약조건:**
- `ck_link_content_type`: content_type IN ('link','article','video','pdf','etc')

---

### folder_suggestion_rule (enrichment 스키마)

자동분류된 카테고리를 기반으로 저장 폴더를 자동 추천하기 위한 규칙. 개인/팀 스코프에 따라 규칙 분리, 자동 채우기 시 우선순위가 높은 규칙부터 적용.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `folder_suggestion_rule_id` | int | not null | identity | PK | - |
| `scope_type` | varchar(10) | not null | 'member' | - | idx_fsr_scope |
| `owner_member_id` | bigint | - | - | uq_fsr(조건부) | idx_fsr_owner |
| `team_id` | int | - | - | - | idx_fsr_team |
| `category_id` | int | not null | - | - | idx_fsr_category |
| `member_folder_id` | int | - | - | - | idx_fsr_member_folder |
| `team_folder_id` | int | - | - | - | idx_fsr_team_folder |
| `priority` | int | not null | 0 | - | idx_fsr_priority |
| `is_active` | boolean | not null | true | - | idx_fsr_active |
| + base_entity | | | | | |

**제약조건:**
- `ck_fsr_scope`: scope_type IN ('member','team')
- `ck_fsr_scope_match`: (member 스코프는 owner_member_id 필수, team 스코프는 team_id 필수)

---

### link_enrichment (enrichment 스키마)

사용자가 URL에 대해 "자동 채우기"를 실행했을 때의 단위. 메타데이터 수집, 자동분류/키워드 추출의 상태·결과·오류·성능 정보를 저장.

| 컬럼명 | 타입 | NULL | 기본값 | Index |
|--------|------|------|--------|-------|
| `link_enrichment_id` | int | not null | identity | - |
| `link_id` | bigint | not null | - | idx_link_enrichment_link_id |
| `request_url` | text | not null | - | - |
| `final_url` | text | - | - | - |
| `fetch_status` | varchar(20) | not null | 'pending' | idx_link_enrichment_fetch_status |
| `classify_status` | varchar(20) | not null | 'pending' | idx_link_enrichment_classify_status |
| `attempt_count` | smallint | not null | 0 | idx_link_enrichment_attempt_count |
| `last_attempt_at` | timestamptz | - | - | idx_link_enrichment_last_attempt_at |
| `error_code` | varchar(50) | - | - | idx_link_enrichment_error_code |
| `error_message` | text | - | - | - |
| `http_status` | int | - | - | - |
| `latency_ms` | int | - | - | - |
| `selected_site_name` | varchar(255) | - | - | - |
| `selected_title` | text | - | - | - |
| `selected_description` | text | - | - | - |
| `fetched_at` | timestamptz | - | - | idx_link_enrichment_fetched_at |
| `predicted_category_id` | int | - | - | idx_link_enrichment_predicted_category_id |
| `predicted_score` | numeric(5,4) | - | - | - |
| `classifier_version` | varchar(50) | - | - | idx_link_enrichment_classifier_version |
| `classified_at` | timestamptz | - | - | idx_link_enrichment_classified_at |
| `keyword_extractor_version` | varchar(50) | - | - | idx_link_enrichment_keyword_extractor_version |
| `keyword_source` | varchar(30) | - | - | idx_link_enrichment_keyword_source |
| `keyword_extracted_at` | timestamptz | - | - | idx_link_enrichment_keyword_extracted_at |
| `suggested_member_folder_id` | int | - | - | idx_link_enrichment_suggested_member_folder_id |
| `suggested_team_folder_id` | int | - | - | idx_link_enrichment_suggested_team_folder_id |
| + base_entity | | | | |

---

### link_enrichment_keyword (enrichment 스키마 - 정규화)

자동 채우기 실행(link_enrichment) 결과로 추출된 추천 키워드/해시태그를 정규화하여 저장. JSON 배열 대신 행 단위로 저장해 검색/집계/랭킹/중복제거가 쉬움.

| 컬럼명 | 타입 | NULL | 기본값 | Unique | Index |
|--------|------|------|--------|--------|-------|
| `link_enrichment_keyword_id` | bigint | not null | identity | PK | - |
| `link_enrichment_id` | int | not null | - | uq_link_enrich_kw(enrichment,keyword) | idx_link_enrich_kw_enrichment |
| `keyword` | varchar(100) | not null | - | - | idx_link_enrich_kw_keyword |
| `score` | numeric(5,4) | - | - | - | - |
| `rank` | smallint | not null | 0 | - | - |
| `source` | varchar(30) | - | - | - | - |
| `created_at` | timestamptz | not null | now() | - | idx_link_enrich_kw_created_at |

---

### link_enrichment_feedback (enrichment 스키마 - 로그)

동채우기 추천 결과에 대해 사용자가 실제로 어떻게 행동했는지(수락/이동/무시)를 기록. 룰 개선/추천 품질 측정의 핵심 데이터.

| 컬럼명 | 타입 | NULL | 기본값 | Index |
|--------|------|------|--------|-------|
| `link_enrichment_feedback_id` | int | not null | identity | - |
| `link_enrichment_id` | int | not null | - | idx_lef_enrichment |
| `member_saved_link_id` | int | - | - | idx_lef_saved_link |
| `action` | varchar(20) | not null | - | idx_lef_action |
| `suggested_member_folder_id` | int | - | - | - |
| `final_member_folder_id` | int | - | - | idx_lef_final_folder |
| `created_at` | timestamptz | not null | now() | idx_lef_created_at |

---

## 버전 정보

- **v0.3.0** (현재): 14개 테이블 완성 (개인 도메인 전체)
- **v0.4.0** (예정): 팀 도메인 7개 테이블 추가

자세한 스키마 정의는 Excel 파일 `searchweb_data_definition_document_v0.3.0.xlsx` 참고.

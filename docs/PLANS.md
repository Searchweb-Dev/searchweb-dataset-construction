# Implementation Plans

각 Phase의 구체적인 구현 계획입니다.

---

## Phase 1: 기본 인프라 구축 (MVP - 현재)

**목표:** 동작하는 기본 시스템 구축 (DB 저장, 조회 가능)

### 1.1 데이터베이스 설정

**작업:**
- PostgreSQL/MySQL 데이터베이스 준비
- SQLAlchemy ORM 모델 정의 (AISite, Job 등)
- 기본 마이그레이션 스크립트 작성

**파일:** `src/models/ai_site.py`
```python
class AISite(Base):
    __tablename__ = "ai_sites"
    
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, index=True)
    category_level_1 = Column(String, index=True)
    category_level_2 = Column(String, index=True)
    category_level_3 = Column(String, nullable=True)
    tags = Column(JSON, index=True)
    is_ai_tool = Column(Boolean, index=True)
    created_at = Column(DateTime, index=True)
    
    __table_args__ = (
        Index('idx_level1_level2', 'category_level_1', 'category_level_2'),
        Index('idx_level1_created', 'category_level_1', 'created_at'),
    )
```

**검수:**
- [ ] DB 마이그레이션 완료
- [ ] ORM 모델 테스트 (INSERT, SELECT)

### 1.2 Connection Pool 설정

**작업:**
- SQLAlchemy 연결 풀 구성
- 연결 풀 크기: pool_size=20, max_overflow=40

**파일:** `src/config/database.py`
```python
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

**검수:**
- [ ] 연결 풀 설정 확인
- [ ] 부하 테스트 (동시 연결 테스트)

### 1.3 Worker 직접 DB 저장

**작업:**
- Celery Worker가 분석 결과를 DB에 직접 저장
- Job 상태 업데이트 (pending → completed)

**파일:** `src/workers/analysis_worker.py`
```python
@celery_app.task
def analyze_task(job_id: str, url: str):
    result = perform_analysis(url)
    site = AISite(
        url=url,
        category_level_1=result['category']['level_1'],
        category_level_2=result['category']['level_2'],
        is_ai_tool=result['is_ai_tool']
    )
    db.add(site)
    db.commit()
```

**검수:**
- [ ] Worker가 DB에 데이터 저장 확인
- [ ] Job 상태 추적 확인

### 1.4 API 엔드포인트 구현

**작업:**
- POST /analyze - 분석 작업 시작
- GET /jobs/{job_id} - 작업 상태 조회
- GET /api/sites - 사이트 목록 조회
- POST /api/bookmarks - 북마크 추가

**파일:** `src/api/routes.py`

**검수:**
- [ ] 각 엔드포인트 동작 확인
- [ ] 입력 검증 및 에러 처리

---

## Phase 2: 읽기 성능 최적화 (3개월 후)

**목표:** Redis 캐싱으로 읽기 응답 시간 10배 개선

### 2.1 Redis 캐시 레이어 추가

**작업:**
- Redis 클라이언트 설정
- 캐시 키 전략 수립

**파일:** `src/config/cache.py`
```python
from redis import Redis

redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True
)
```

**검수:**
- [ ] Redis 연결 확인
- [ ] 캐시 읽기/쓰기 테스트

### 2.2 캐시 적용 - 사이트 목록 조회

**작업:**
- GET /api/sites 엔드포인트에 캐싱 로직 추가
- 캐시 키: `sites:list:{level_1}:{level_2}`
- TTL: 1시간

**파일:** `src/api/routes.py` (수정)
```python
@app.get("/api/sites")
async def list_sites(level_1: str = None, level_2: str = None):
    # 캐시 키 생성
    if level_1 and level_2:
        cache_key = f"sites:list:{level_1}:{level_2}"
    elif level_1:
        cache_key = f"sites:list:{level_1}"
    else:
        cache_key = "sites:list:all"
    
    # Redis 캐시 확인
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # DB 조회
    query = db.query(AISite)
    if level_1:
        query = query.filter_by(category_level_1=level_1)
    if level_2:
        query = query.filter_by(category_level_2=level_2)
    sites = query.all()
    
    # 캐싱 (1시간 TTL)
    redis_client.setex(cache_key, 3600, json.dumps([s.to_dict() for s in sites]))
    
    return sites
```

**검수:**
- [ ] 캐시 히트/미스 로깅
- [ ] 응답 시간 측정 (DB만 vs 캐시)

### 2.3 캐시 무효화 전략

**작업:**
- Worker가 DB 저장 후 관련 캐시 무효화
- 계층적 무효화: 전체 → 레벨1 → 레벨1+레벨2

**파일:** `src/workers/analysis_worker.py` (수정)
```python
@celery_app.task
def analyze_task(job_id: str, url: str):
    result = perform_analysis(url)
    site = AISite(...)
    db.add(site)
    db.commit()
    
    # 캐시 무효화
    level_1 = result['category']['level_1']
    level_2 = result['category']['level_2']
    redis_client.delete(f"sites:list:{level_1}:{level_2}")
    redis_client.delete(f"sites:list:{level_1}")
    redis_client.delete("sites:list:all")
```

**검수:**
- [ ] 데이터 추가 후 캐시 무효화 확인
- [ ] 다음 조회에서 최신 데이터 반환 확인

### 2.4 모니터링

**작업:**
- 캐시 히트율 로깅
- 응답 시간 메트릭 수집

**파일:** `src/observability/metrics.py`

**검수:**
- [ ] 캐시 히트율 > 80% 확인
- [ ] 읽기 성능 10배 개선 확인

---

## Phase 3: 쓰기 성능 최적화 (1년 후)

**목표:** Write Queue + Batch Insert로 쓰기 성능 5~10배 개선

### 3.1 Redis Write Queue 구현

**작업:**
- Worker가 분석 결과를 Redis 큐에만 저장 (빠름)
- Job 상태를 Redis에서 조회

**파일:** `src/workers/analysis_worker.py` (수정)
```python
@celery_app.task
def analyze_task(job_id: str, url: str):
    result = perform_analysis(url)
    
    # Redis 큐에만 저장 (빠름)
    redis_client.rpush("db_write_queue", json.dumps({
        "job_id": job_id,
        "result": result
    }))
    
    # Job 상태 업데이트 (빠름)
    redis_client.set(f"job:{job_id}:status", "completed")
    redis_client.expire(f"job:{job_id}:status", 24 * 3600)
```

**검수:**
- [ ] 분석 작업 응답 시간 측정 (이전 단계 대비)
- [ ] Redis 큐 크기 모니터링

### 3.2 Batch Insert Worker 구현

**작업:**
- 별도의 Worker가 주기적으로 Redis 큐에서 데이터를 읽음
- 100개 단위로 배치 INSERT 실행

**파일:** `src/workers/batch_writer.py`
```python
@celery_app.task
def batch_write_task():
    db = SessionLocal()
    batch_size = 100
    results = []
    
    # 큐에서 최대 100개 읽기
    for _ in range(batch_size):
        item = redis_client.lpop("db_write_queue")
        if item:
            results.append(json.loads(item))
    
    # 배치 INSERT
    if results:
        sites = [
            AISite(
                url=r['result']['url'],
                category_level_1=r['result']['category']['level_1'],
                # ...
            )
            for r in results
        ]
        db.bulk_insert_mappings(AISite, [s.__dict__ for s in sites])
        db.commit()
    
    db.close()
```

**검수:**
- [ ] Batch INSERT 성능 측정
- [ ] 데이터 손실 없음 확인

### 3.3 두 시스템 간 일관성

**작업:**
- 사용자는 Redis의 Job 상태로 완료 여부 확인
- DB에는 비동기로 저장

**파일:** `src/api/routes.py` (수정)
```python
@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    # Redis에서 상태 조회 (빠름)
    status = redis_client.get(f"job:{job_id}:status")
    
    if status == "completed":
        # DB에서 결과 조회 (배치 저장 완료 후)
        site = db.query(AISite).filter_by(job_id=job_id).first()
        return {"status": status, "data": site}
    
    return {"status": status}
```

**검수:**
- [ ] Job 상태 조회 순서 확인
- [ ] Redis와 DB 간 지연 시간 허용 범위 확인

---

## Phase 4: 대규모 확장 (2년 후)

**목표:** Read Replica로 읽기/쓰기 완전 분산

### 4.1 데이터베이스 복제 구성

**작업:**
- Master DB (쓰기용)
- Replica DB (읽기용)
- Replication lag 모니터링

**파일:** `src/config/database.py` (수정)
```python
engine_write = create_engine("postgresql://master-db:5432/mydb")
engine_read = create_engine("postgresql://replica-db:5432/mydb")

SessionWrite = sessionmaker(bind=engine_write)
SessionRead = sessionmaker(bind=engine_read)
```

### 4.2 읽기/쓰기 분리

**작업:**
- 모든 쓰기는 Master로 -> Worker, API POST
- 모든 읽기는 Replica로 -> API GET

**파일:** `src/api/routes.py` (수정)
```python
@app.get("/api/sites")
async def list_sites():
    # Replica에서 읽기
    db = SessionRead()
    sites = db.query(AISite).all()
    return sites

@app.post("/api/sites")
async def create_site():
    # Master에 쓰기
    db = SessionWrite()
    # ...
```

### 4.3 모니터링

**작업:**
- Replication lag 모니터링
- 읽기 쿼리 분산 확인

**검수:**
- [ ] Replica lag < 1초 확인
- [ ] 읽기 부하 감소 확인

---

## 구현 순서

| Phase | 예상 기간 | 우선순위 | 상태 |
|-------|---------|---------|-----|
| 1 | 4주 | ⭐⭐⭐ | 현재 진행 중 |
| 2 | 2주 | ⭐⭐ | 계획 중 |
| 3 | 3주 | ⭐⭐ | 계획 중 |
| 4 | 4주 | ⭐ | 계획 중 |

---

## 성능 지표

| 지표 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|--------|--------|--------|---------|
| **평균 읽기 응답시간** | 500ms | 50ms | 50ms | 30ms |
| **평균 쓰기 응답시간** | 2000ms | 2000ms | 200ms | 200ms |
| **DB 연결 풀 활용률** | 60% | 40% | 30% | 20% |
| **캐시 히트율** | - | 85% | 85% | 85% |

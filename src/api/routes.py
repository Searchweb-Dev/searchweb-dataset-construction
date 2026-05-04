"""AI 사이트 분석 API 라우트."""

from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.models import AnalysisJob, AISite
from src.db.session import SessionLocal
from src.api.deps import verify_api_key
from src.schemas import AnalysisJobRequest, AnalysisJobResponse, AISiteResponse
from src.workers.analyze_task import analyze_website

router = APIRouter()


def get_db() -> Session:
    """DB 세션."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/analyze", status_code=202, response_model=AnalysisJobResponse)
def analyze(
    request: AnalysisJobRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """분석 요청 (비동기 작업 생성)."""
    url = str(request.url)

    # 기존 분석 결과 확인 (재분석 강제 아님)
    if not request.force_reanalyze:
        existing = db.query(AISite).filter(AISite.url == url).first()
        if existing:
            # 기존 결과가 있으면 해당 job 반환
            job = db.query(AnalysisJob).filter(
                AnalysisJob.site_id == existing.site_id,
                AnalysisJob.status == "success"
            ).order_by(AnalysisJob.completed_at.desc()).first()

            if job:
                return AnalysisJobResponse(
                    job_id=job.job_id,
                    url=job.url,
                    status=job.status,
                    created_at=job.created_at,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    retry_count=job.retry_count,
                    error_message=job.error_message,
                )

    # 새 작업 생성
    job = AnalysisJob(
        job_id=uuid4(),
        url=url,
        status="pending",
        retry_count=0,
        request_source="api",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Celery 비동기 작업 시작
    analyze_website.delay(str(job.job_id), url)

    return AnalysisJobResponse(
        job_id=job.job_id,
        url=job.url,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        retry_count=job.retry_count,
        error_message=job.error_message,
    )


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
def get_job_status(
    job_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """분석 작업 상태 조회."""
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_uuid).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 결과 데이터 로드
    result = None
    if job.status == "success" and job.site_id:
        site = db.query(AISite).filter(AISite.site_id == job.site_id).first()
        if site:
            # 카테고리 및 태그 로드
            from src.db.models import AICategory, AITag

            categories = db.query(AICategory).filter(
                AICategory.site_id == site.site_id
            ).all()
            tags = db.query(AITag).filter(
                AITag.site_id == site.site_id
            ).all()

            from src.schemas import CategoryResponse, ScoreResponse

            result = AISiteResponse(
                site_id=site.site_id,
                url=site.url,
                is_ai_tool=site.is_ai_tool,
                title=site.title,
                description=site.description,
                summary_ko=site.summary_ko,
                categories=[
                    CategoryResponse(
                        level_1=c.level_1,
                        level_2=c.level_2,
                        level_3=c.level_3,
                        is_primary=c.is_primary,
                    )
                    for c in categories
                ],
                tags=[t.tag_name for t in tags],
                scores=ScoreResponse(
                    utility=site.score_utility,
                    trust=site.score_trust,
                    originality=site.score_originality,
                ),
                last_analyzed_at=site.last_analyzed_at,
            )

    return AnalysisJobResponse(
        job_id=job.job_id,
        url=job.url,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        retry_count=job.retry_count,
        error_message=job.error_message,
        result=result,
    )

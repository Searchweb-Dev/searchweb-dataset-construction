"""AI 사이트 분석 API 라우트."""

import json
import os
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.models import AnalysisJob, AISite, AICategory, AITag
from src.db.session import get_db
from src.api.deps import verify_api_key
from src.schemas import AnalysisJobRequest, AnalysisJobResponse, AISiteResponse, BatchAnalysisRequest, BatchAnalysisResponse, CategoryResponse, ScoreResponse
from src.workers.analyze_task import analyze_website, analyze_ai_tools_batch
from src.core.url import normalize_url
from src.core.enums import JobStatus

router = APIRouter()


@router.post("/analyze", status_code=202, response_model=AnalysisJobResponse)
def analyze(
    request: AnalysisJobRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """단일 URL을 비동기로 분석하는 작업을 생성한다.

    이미 분석된 URL이 있으면 기존 성공 job을 즉시 반환한다.
    force_reanalyze=true이면 기존 결과를 무시하고 새 작업을 생성한다.
    작업 결과는 GET /jobs/{job_id}로 폴링해 확인한다.

    Args:
        request: 분석할 URL과 재분석 강제 여부.
        api_key: API 키 검증 의존성.
        db: DB 세션 의존성.

    Returns:
        생성된 분석 작업 정보 (status=pending 또는 기존 success job).

    Raises:
        HTTPException 422: URL 형식 오류.
    """
    url = normalize_url(str(request.url))

    # 기존 분석 결과 확인 (재분석 강제 아님)
    if not request.force_reanalyze:
        existing = db.query(AISite).filter(AISite.url == url).first()
        if existing:
            # 기존 결과가 있으면 해당 job 반환
            job = db.query(AnalysisJob).filter(
                AnalysisJob.site_id == existing.site_id,
                AnalysisJob.status == JobStatus.SUCCESS
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
        status=JobStatus.PENDING,
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


@router.post("/analyze/batch", status_code=202, response_model=BatchAnalysisResponse)
def analyze_batch(
    request: BatchAnalysisRequest,
    api_key: str = Depends(verify_api_key),
):
    """data/ai-tools.json의 URL 목록을 일괄 비동기 분석한다.

    limit 미입력 시 전체 항목을, 입력 시 해당 개수만 분석한다.
    이미 분석된 URL은 기본적으로 건너뛰며, force_reanalyze=true이면 전체 재분석한다.
    분석 완료 후 결과가 data/ 디렉토리에 타임스탬프 파일 한 개로 저장된다.

    Args:
        request: 분석 항목 수 제한(limit)과 재분석 강제 여부.
        api_key: API 키 검증 의존성.

    Returns:
        전체 항목 수, 분석 대상 수, 작업 접수 안내 메시지.

    Raises:
        HTTPException 500: ai-tools.json 파일을 찾을 수 없는 경우.
        HTTPException 422: 요청 파라미터 형식 오류.
    """
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "ai-tools.json",
    )
    if not os.path.isfile(json_path):
        raise HTTPException(status_code=500, detail="ai-tools.json 파일을 찾을 수 없습니다.")

    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    total = len(items)
    target = min(request.limit, total) if request.limit is not None else total

    analyze_ai_tools_batch.delay(request.limit, request.force_reanalyze)

    return BatchAnalysisResponse(
        total=total,
        target=target,
        message=f"{target}건 분석을 백그라운드에서 시작했습니다. 완료 후 data/ 디렉토리에 결과 파일이 생성됩니다.",
    )


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
def get_job_status(
    job_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """분석 작업의 현재 상태와 결과를 조회한다.

    작업이 완료(status=success)된 경우 분석 결과(AISite 정보)를 함께 반환한다.
    완료 전이면 result 필드는 null이다.

    Args:
        job_id: 조회할 작업의 UUID 문자열.
        api_key: API 키 검증 의존성.
        db: DB 세션 의존성.

    Returns:
        작업 상태 및 완료 시 분석 결과(site 정보, 카테고리, 태그, 점수).

    Raises:
        HTTPException 400: job_id가 유효한 UUID 형식이 아닌 경우.
        HTTPException 404: 해당 job_id의 작업이 존재하지 않는 경우.
    """
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_uuid).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 결과 데이터 로드
    result = None
    if job.status == JobStatus.SUCCESS and job.site_id:
        site = db.query(AISite).filter(AISite.site_id == job.site_id).first()
        if site:
            categories = db.query(AICategory).filter(
                AICategory.site_id == site.site_id
            ).all()
            tags = db.query(AITag).filter(
                AITag.site_id == site.site_id
            ).all()

            result = AISiteResponse(
                site_id=site.site_id,
                url=site.url,
                is_ai_tool=site.is_ai_tool,
                title=site.title,
                description=site.description,
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

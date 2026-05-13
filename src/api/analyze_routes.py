"""비동기 URL 분석 요청 API 라우트."""

from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import verify_api_key
from src.core.enums import JobStatus
from src.core.url import normalize_url
from src.db.models import AISite, AnalysisJob
from src.db.session import get_db
from src.schemas import (
    AnalysisJobRequest,
    AnalysisJobResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
)
from src.workers.analyze_task import analyze_ai_tools_batch, analyze_website

router = APIRouter()


@router.post("", status_code=202, response_model=AnalysisJobResponse)
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

    if not request.force_reanalyze:
        existing = db.query(AISite).filter(AISite.url == url).first()
        if existing:
            job = (
                db.query(AnalysisJob)
                .filter(
                    AnalysisJob.site_id == existing.site_id,
                    AnalysisJob.status == JobStatus.SUCCESS,
                )
                .order_by(AnalysisJob.completed_at.desc())
                .first()
            )
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


@router.post("/batch", status_code=202, response_model=BatchAnalysisResponse)
def analyze_batch(
    request: BatchAnalysisRequest,
    api_key: str = Depends(verify_api_key),
):
    """URL 목록을 일괄 비동기 분석한다.

    이미 분석된 URL은 기본적으로 건너뛰며, force_reanalyze=true이면 전체 재분석한다.
    분석 완료 후 결과가 data/ 디렉토리에 타임스탬프 파일 한 개로 저장된다.

    Args:
        request: 분석할 URL 목록(최대 500개)과 재분석 강제 여부.
        api_key: API 키 검증 의존성.

    Returns:
        전체 URL 수, 접수된 URL 수, 작업 접수 안내 메시지.
    """
    urls = [str(u) for u in request.urls]
    analyze_ai_tools_batch.delay(urls, request.force_reanalyze)

    return BatchAnalysisResponse(
        total=len(urls),
        accepted=len(urls),
        message=f"{len(urls)}건 분석을 백그라운드에서 시작했습니다. 완료 후 data/ 디렉토리에 결과 파일이 생성됩니다.",
    )

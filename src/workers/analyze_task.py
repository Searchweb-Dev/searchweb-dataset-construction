"""웹사이트 AI 판별 비동기 작업."""

import logging
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models.base import Base
from src.db.models import AnalysisJob
from src.ai.detector import AIDetector
from src.workers.celery_app import app
from src.core.config import get_db_url

logger = logging.getLogger(__name__)

# DB 세션 생성
engine = create_engine(get_db_url())
SessionLocal = sessionmaker(bind=engine)


@app.task(bind=True, max_retries=3)
def analyze_website(self, job_id: str, url: str) -> dict[str, Any]:
    """
    웹사이트 분석 작업.
    
    Args:
        job_id: 분석 작업 ID (UUID)
        url: 분석 대상 URL
    
    Returns:
        분석 결과 딕셔너리
    """
    db = SessionLocal()
    
    try:
        # 1. Job 상태 업데이트 (processing)
        job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
        if not job:
            logger.error(f"Job을 찾을 수 없음: {job_id}")
            return {"error": "Job not found"}

        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()
        logger.info(f"Job 상태 업데이트 (processing): {job_id}")

        # 2. AI 판별 실행
        detector = AIDetector(db)
        result = detector.detect_and_save(url)

        if not result:
            raise Exception("분석 실패")

        # 3. Job 상태 업데이트 (success)
        job.status = "success"
        job.completed_at = datetime.utcnow()
        job.site_id = result.get("site_id")
        db.commit()
        logger.info(f"분석 완료: {job_id} -> {result}")

        return {
            "job_id": str(job_id),
            "status": "success",
            "site_id": result.get("site_id"),
            "is_ai_tool": result.get("is_ai_tool"),
        }

    except Exception as e:
        logger.error(f"분석 작업 실패: {e}")
        db.rollback()

        # Job 상태 업데이트
        job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
        if job:
            job.retry_count = self.request.retries
            job.error_message = str(e)

            if self.request.retries < self.max_retries:
                job.status = "pending"
                logger.info(f"재시도 대기: {job_id} (시도: {self.request.retries + 1}/{self.max_retries})")
            else:
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                logger.error(f"최종 실패: {job_id}")

            db.commit()

        # 재시도
        if self.request.retries < self.max_retries:
            raise self.retry(exc=Exception(str(e)), countdown=60 * (self.request.retries + 1))

        return {
            "job_id": str(job_id),
            "status": "failed",
            "error": str(e),
        }

    finally:
        db.close()

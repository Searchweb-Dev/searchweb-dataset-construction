"""Celery 분석 작업 테스트."""

from uuid import uuid4
import pytest


def test_analyze_task_exists():
    """분석 작업 존재 확인."""
    from src.workers.analyze_task import analyze_website
    
    assert analyze_website is not None
    assert hasattr(analyze_website, "name")


def test_celery_app_configured():
    """Celery 앱 설정 확인."""
    from src.workers.celery_app import app
    
    assert app is not None
    assert app.conf.broker_url is not None
    assert app.conf.result_backend is not None

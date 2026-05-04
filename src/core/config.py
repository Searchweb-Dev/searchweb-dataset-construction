"""애플리케이션 설정."""

import os
from functools import lru_cache


@lru_cache
def get_db_url() -> str:
    """DB URL 반환."""
    env = os.getenv("ENV", "development")
    
    if env == "production":
        return os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/ai_detector",
        )
    
    return os.getenv(
        "DATABASE_URL",
        "sqlite:///./test.db",
    )


def get_api_key() -> str:
    """API 키 반환 (기본값)."""
    return os.getenv("API_KEY", "test-api-key-change-in-production")


def get_claude_api_key() -> str:
    """Claude API 키 반환."""
    return os.getenv("ANTHROPIC_API_KEY", "")

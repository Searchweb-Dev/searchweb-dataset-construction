"""애플리케이션 설정."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


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


def get_llm_provider() -> str:
    """LLM 프로바이더 반환. gemini | claude"""
    return os.getenv("LLM_PROVIDER", "gemini")


def get_gemini_api_key() -> str:
    """Gemini API 키 반환."""
    return os.getenv("GEMINI_API_KEY", "")


def get_claude_api_key() -> str:
    """Claude API 키 반환."""
    return os.getenv("ANTHROPIC_API_KEY", "")

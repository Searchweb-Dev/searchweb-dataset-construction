from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수(.env 포함)에서 로드되는 애플리케이션 설정 객체."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "threads-url-pipeline"
    app_env: str = "dev"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg2://postgres:your_strong_password@127.0.0.1:5432/mydb"

    threads_use_mock: bool = True
    threads_api_token: str | None = None
    threads_base_url: str = "https://graph.threads.net"
    threads_search_path: str = "/v1.0/keyword_search"
    threads_search_type: str = "TOP"
    threads_search_mode: str = "KEYWORD"
    threads_fields: str = (
        "id,text,media_type,permalink,timestamp,username,has_replies,is_quote_post,is_reply"
    )
    threads_timeout_seconds: int = 20
    threads_result_limit: int = 25

    default_keywords_csv: str = "AI, AI 서비스,AI 툴,AI 추천,생산성 툴,무료 AI 사이트"
    aggregate_top_n: int = 10

    short_url_expand_enabled: bool = False
    subdomain_policy: str = Field(default="registered", description="registered|full")

    @property
    def default_keywords(self) -> List[str]:
        """기본 키워드 CSV 문자열을 공백 제거된 리스트로 변환해 반환한다."""
        return [item.strip() for item in self.default_keywords_csv.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """설정 객체를 캐시하여 재사용한다."""
    return Settings()

from __future__ import annotations

from typing import Optional

import typer

from app.clients.base import BaseThreadsClient
from app.clients.threads_api import ThreadsApiClient
from app.clients.threads_mock import MockThreadsClient
from app.config import get_settings
from app.db import get_session
from app.logging import configure_logging, get_logger
from app.repositories.posts import PostsRepository
from app.repositories.tools import ToolsRepository
from app.repositories.urls import URLsRepository
from app.services.aggregator import AggregatorService, format_console_table
from app.services.collector import CollectorService
from app.services.tool_extractor import ToolExtractionService
from app.services.url_extractor import URLExtractionService

cli = typer.Typer(help="Threads URL extraction MVP CLI")
logger = get_logger(__name__)


def _parse_keywords(keyword_input: Optional[str]) -> list[str]:
    """쉼표로 구분된 키워드 문자열을 파싱하고, 없으면 설정의 기본 키워드를 사용한다."""
    settings = get_settings()
    if keyword_input:
        return [item.strip() for item in keyword_input.split(",") if item.strip()]
    return settings.default_keywords


def _build_client() -> BaseThreadsClient:
    """런타임 설정에 따라 Threads 클라이언트를 생성한다(기본값: mock)."""
    settings = get_settings()
    if settings.threads_use_mock:
        return MockThreadsClient()

    if not settings.threads_api_token:
        logger.warning("threads_api_token_empty_fallback_to_mock")
        return MockThreadsClient()

    return ThreadsApiClient(
        base_url=settings.threads_base_url,
        search_path=settings.threads_search_path,
        access_token=settings.threads_api_token,
        search_type=settings.threads_search_type,
        search_mode=settings.threads_search_mode,
        fields=settings.threads_fields,
        timeout_seconds=settings.threads_timeout_seconds,
    )


@cli.command("collect")
def collect_command(
    keywords: Optional[str] = typer.Option(None, help='Comma-separated keywords, e.g. "AI 툴,AI 서비스"'),
    limit: int = typer.Option(25, min=1, max=100),
) -> None:
    """지정한 키워드로 게시글을 수집하고 posts 테이블에 upsert한다."""
    settings = get_settings()
    configure_logging(settings.log_level)
    kw = _parse_keywords(keywords)

    client = _build_client()
    posts_repo = PostsRepository()
    collector = CollectorService(client=client, posts_repo=posts_repo)

    with get_session() as session:
        stats = collector.collect(session=session, keywords=kw, limit_per_keyword=limit)
    typer.echo(f"collect done: {stats}")


@cli.command("extract-urls")
def extract_urls_command(limit: int = typer.Option(0, min=0)) -> None:
    """저장된 게시글에서 URL을 추출하고 정규화 URL/도메인 결과를 저장한다."""
    settings = get_settings()
    configure_logging(settings.log_level)

    posts_repo = PostsRepository()
    urls_repo = URLsRepository()
    service = URLExtractionService(
        posts_repo=posts_repo,
        urls_repo=urls_repo,
        subdomain_policy=settings.subdomain_policy,
    )

    with get_session() as session:
        stats = service.run(session=session, limit=(limit or None))
    typer.echo(f"extract-urls done: {stats}")


@cli.command("extract-tools")
def extract_tools_command(
    only_without_urls: bool = typer.Option(True, help="Extract only for posts without URLs"),
    limit: int = typer.Option(0, min=0),
) -> None:
    """게시글에서 툴/서비스명 후보를 추출하고 중복 제거 후 저장한다."""
    settings = get_settings()
    configure_logging(settings.log_level)

    service = ToolExtractionService(
        posts_repo=PostsRepository(),
        urls_repo=URLsRepository(),
        tools_repo=ToolsRepository(),
    )

    with get_session() as session:
        stats = service.run(session=session, only_without_urls=only_without_urls, limit=(limit or None))
    typer.echo(f"extract-tools done: {stats}")


@cli.command("aggregate")
def aggregate_command(top_n: Optional[int] = typer.Option(None, min=1)) -> None:
    """집계 쿼리를 실행하고 도메인/툴/빈도 표를 출력한다."""
    settings = get_settings()
    configure_logging(settings.log_level)
    n = top_n or settings.aggregate_top_n

    service = AggregatorService()
    with get_session() as session:
        top_domains = service.get_top_domains(session=session, top_n=n)
        top_tools = service.get_top_tools(session=session, top_n=n)
        keyword_domains = service.get_keyword_domain_frequency(session=session, top_n=n)

    typer.echo("\n[Top Domains]")
    typer.echo(format_console_table(["domain", "mention_count", "unique_authors"], top_domains))
    typer.echo("\n[Top Tools]")
    typer.echo(format_console_table(["tool_name", "mention_count"], top_tools))
    typer.echo("\n[Keyword x Domain]")
    typer.echo(format_console_table(["keyword", "domain", "mention_count"], keyword_domains))


@cli.command("run-all")
def run_all_command(
    keywords: Optional[str] = typer.Option(None, help='Comma-separated keywords, e.g. "AI 툴,AI 서비스"'),
    limit: int = typer.Option(25, min=1, max=100),
    top_n: Optional[int] = typer.Option(None, min=1),
) -> None:
    """collect -> URL 추출 -> 툴 추출 -> 집계를 한 번에 실행한다."""
    settings = get_settings()
    configure_logging(settings.log_level)
    kw = _parse_keywords(keywords)
    n = top_n or settings.aggregate_top_n

    client = _build_client()
    collector = CollectorService(client=client, posts_repo=PostsRepository())
    url_service = URLExtractionService(
        posts_repo=PostsRepository(),
        urls_repo=URLsRepository(),
        subdomain_policy=settings.subdomain_policy,
    )
    tool_service = ToolExtractionService(
        posts_repo=PostsRepository(),
        urls_repo=URLsRepository(),
        tools_repo=ToolsRepository(),
    )
    aggregator = AggregatorService()

    with get_session() as session:
        collect_stats = collector.collect(session=session, keywords=kw, limit_per_keyword=limit)
        url_stats = url_service.run(session=session)
        tool_stats = tool_service.run(session=session, only_without_urls=True)
        top_domains = aggregator.get_top_domains(session=session, top_n=n)
        top_tools = aggregator.get_top_tools(session=session, top_n=n)

    typer.echo(f"collect: {collect_stats}")
    typer.echo(f"extract-urls: {url_stats}")
    typer.echo(f"extract-tools: {tool_stats}")
    typer.echo("\n[Top Domains]")
    typer.echo(format_console_table(["domain", "mention_count", "unique_authors"], top_domains))
    typer.echo("\n[Top Tools]")
    typer.echo(format_console_table(["tool_name", "mention_count"], top_tools))


if __name__ == "__main__":
    cli()

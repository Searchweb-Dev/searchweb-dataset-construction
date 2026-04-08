from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base
from app.models.post import Post
from app.models.tool import ExtractedTool
from app.models.url import ExtractedURL
from app.services.aggregator import AggregatorService


def _setup_session() -> Session:
    """집계 테스트용 인메모리 SQLite 세션을 생성한다."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return factory()


def test_aggregator_domain_and_tool_counts() -> None:
    """도메인/툴 집계 결과가 기대한 순위와 건수를 반환하는지 검증한다."""
    session = _setup_session()
    now = datetime.now(timezone.utc)

    p1 = Post(
        platform_post_id="p1",
        keyword="AI 툴",
        author_handle="u1",
        content="hello",
        raw_json={"id": "p1"},
        collected_at=now,
    )
    p2 = Post(
        platform_post_id="p2",
        keyword="AI 툴",
        author_handle="u2",
        content="hello2",
        raw_json={"id": "p2"},
        collected_at=now,
    )
    session.add_all([p1, p2])
    session.flush()

    session.add_all(
        [
            ExtractedURL(post_id=p1.id, raw_url="https://a.com", normalized_url="https://a.com/", domain="a.com"),
            ExtractedURL(post_id=p2.id, raw_url="https://a.com/x", normalized_url="https://a.com/x", domain="a.com"),
            ExtractedURL(post_id=p2.id, raw_url="https://b.com", normalized_url="https://b.com/", domain="b.com"),
            ExtractedTool(post_id=p1.id, tool_name="Cursor", normalized_tool_name="cursor", confidence=0.9),
            ExtractedTool(post_id=p2.id, tool_name="Cursor", normalized_tool_name="cursor", confidence=0.9),
            ExtractedTool(post_id=p2.id, tool_name="Perplexity", normalized_tool_name="perplexity", confidence=0.8),
        ]
    )
    session.commit()

    service = AggregatorService()
    domains = service.get_top_domains(session, top_n=5)
    tools = service.get_top_tools(session, top_n=5)
    kw_domain = service.get_keyword_domain_frequency(session, top_n=5)

    assert domains[0]["domain"] == "a.com"
    assert domains[0]["mention_count"] == 2
    assert tools[0]["tool_name"] == "cursor"
    assert tools[0]["mention_count"] == 2
    assert len(kw_domain) >= 1

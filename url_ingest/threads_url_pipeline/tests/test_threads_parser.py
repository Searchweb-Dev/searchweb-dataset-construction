from app.clients.threads_mock import MOCK_POSTS
from app.parsers.threads_parser import parse_threads_item, parse_threads_items


def test_parse_threads_item_with_standard_fields() -> None:
    """표준 필드(id/text/username) 응답이 정상 파싱되는지 검증한다."""
    item = {"id": "123", "text": "hello", "username": "user1"}
    parsed = parse_threads_item(item, keyword="AI 툴")
    assert parsed is not None
    assert parsed.platform_post_id == "123"
    assert parsed.content == "hello"
    assert parsed.author_handle == "user1"


def test_parse_threads_item_with_alternative_fields() -> None:
    """대체 필드(post_id/content/author.username) 매핑이 동작하는지 검증한다."""
    item = {"post_id": "alt_1", "content": "body", "author": {"username": "alice"}}
    parsed = parse_threads_item(item, keyword="AI 서비스")
    assert parsed is not None
    assert parsed.platform_post_id == "alt_1"
    assert parsed.content == "body"
    assert parsed.author_handle == "alice"


def test_parse_threads_items_from_mock_data() -> None:
    """mock 데이터 리스트 파싱 시 유효한 게시글 ID가 유지되는지 검증한다."""
    parsed = parse_threads_items(MOCK_POSTS, keyword="AI 추천")
    assert len(parsed) >= 10
    assert all(item.platform_post_id for item in parsed)

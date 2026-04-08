from app.services.domain_normalizer import apply_subdomain_policy, normalize_url


def test_normalize_url_removes_tracking_and_www() -> None:
    """추적 파라미터와 www 접두어 제거가 정상 동작하는지 검증한다."""
    normalized = normalize_url("https://www.Example.com/path?utm_source=threads&x=1#section")
    assert normalized is not None
    assert normalized.normalized_url == "https://example.com/path?x=1"
    assert normalized.domain == "example.com"


def test_normalize_url_supports_www_without_scheme() -> None:
    """스킴 없는 www URL 입력을 https 기준으로 정규화하는지 검증한다."""
    normalized = normalize_url("www.notion.so/product?fbclid=abc")
    assert normalized is not None
    assert normalized.normalized_url == "https://notion.so/product"
    assert normalized.domain == "notion.so"


def test_subdomain_policy_full() -> None:
    """서브도메인 정책(full/registered) 분기 동작을 검증한다."""
    assert apply_subdomain_policy("news.example.com", policy="full") == "news.example.com"
    assert apply_subdomain_policy("news.example.com", policy="registered") == "example.com"

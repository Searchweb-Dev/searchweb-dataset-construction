from app.services.url_extractor import extract_urls_from_text


def test_extract_urls_from_text_mixed_language_and_patterns() -> None:
    """한글/영문 혼합 본문에서 다양한 URL 패턴이 추출되는지 검증한다."""
    text = (
        "AI 툴 추천: https://www.perplexity.ai, "
        "그리고 www.notion.so/workspace. "
        "마지막은 https://gamma.app/path?utm_source=threads!"
    )
    urls = extract_urls_from_text(text)
    assert "https://www.perplexity.ai" in urls
    assert "www.notion.so/workspace" in urls
    assert "https://gamma.app/path?utm_source=threads" in urls


def test_extract_urls_deduplicates_and_trims_punctuation() -> None:
    """중복 URL 제거와 후행 문장부호 제거가 동작하는지 검증한다."""
    text = "visit https://example.com. again https://example.com)"
    urls = extract_urls_from_text(text)
    assert urls == ["https://example.com"]

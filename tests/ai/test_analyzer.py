"""Claude API 클라이언트 테스트."""

import json
from unittest.mock import Mock, patch
import pytest

from src.ai.analyzer import WebAnalyzer


def test_analyzer_initialization():
    """분석기 초기화 테스트."""
    analyzer = WebAnalyzer()
    assert analyzer.model == "claude-sonnet-4-6"
    assert analyzer.client is not None


def test_parse_response_valid_json():
    """응답 파싱 - 유효한 JSON."""
    analyzer = WebAnalyzer()
    
    response_text = """
    분석 결과입니다:
    {
        "is_ai_tool": true,
        "title": "Test AI",
        "description": "테스트 AI 도구",
        "categories": [{"level_1": "AI", "level_2": "Chat", "level_3": "LLM", "is_primary": true}],
        "tags": ["chatbot", "nlp"],
        "scores": {"utility": 8, "trust": 9, "originality": 7},
        "confidence": 0.95
    }
    """
    
    result = analyzer._parse_response(response_text)
    
    assert result["is_ai_tool"] is True
    assert result["title"] == "Test AI"
    assert result["confidence"] == 0.95


def test_parse_response_invalid_json():
    """응답 파싱 - 잘못된 JSON."""
    analyzer = WebAnalyzer()
    
    response_text = "응답에 JSON이 없습니다."
    result = analyzer._parse_response(response_text)
    
    assert result["is_ai_tool"] is False
    assert result["title"] == "Unknown"


def test_analysis_prompt_generation():
    """분석 프롬프트 생성 테스트."""
    analyzer = WebAnalyzer()
    
    url = "https://example.com"
    content = "Test content"
    
    prompt = analyzer._build_analysis_prompt(url, content)
    
    assert url in prompt
    assert "AI 도구" in prompt
    assert "JSON" in prompt


@patch("src.ai.analyzer.Anthropic")
def test_analyze_website_success(mock_anthropic):
    """웹사이트 분석 - 성공 케이스."""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = json.dumps({
        "is_ai_tool": True,
        "title": "Claude",
        "description": "AI Assistant",
        "categories": [],
        "tags": ["ai", "chat"],
        "scores": {"utility": 9, "trust": 9, "originality": 8},
        "confidence": 0.98
    })
    
    mock_client = Mock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client
    
    analyzer = WebAnalyzer()
    result = analyzer.analyze_website(
        url="https://claude.ai",
        page_content="Claude is an AI assistant..."
    )
    
    assert result["is_ai_tool"] is True
    assert result["title"] == "Claude"
    assert result["confidence"] == 0.98

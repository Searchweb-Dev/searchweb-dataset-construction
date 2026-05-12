"""
기능 4: get_analyzer() 분기 로직 테스트.

CLASSIFIER_MODE=rule / llm 각각의 분기 동작을 검증한다.
외부 네트워크 호출이나 실제 LLM API 호출 없이 실행된다.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


class TestGetAnalyzerRuleBranch:
    """CLASSIFIER_MODE=rule 분기 테스트."""

    def test_classifier_mode_rule_returns_rule_analyzer(self) -> None:
        """CLASSIFIER_MODE=rule 이면 RuleAnalyzer 인스턴스를 반환해야 한다."""
        # Arrange
        with patch.dict(os.environ, {"CLASSIFIER_MODE": "rule"}):
            # Act
            from src.ai.analyzer import get_analyzer
            from src.rule.analyzer import RuleAnalyzer
            analyzer = get_analyzer()

        # Assert
        assert isinstance(analyzer, RuleAnalyzer)

    def test_rule_analyzer_has_analyze_website_method(self) -> None:
        """CLASSIFIER_MODE=rule 이면 반환된 분석기에 analyze_website 메서드가 있어야 한다."""
        # Arrange
        with patch.dict(os.environ, {"CLASSIFIER_MODE": "rule"}):
            # Act
            from src.ai.analyzer import get_analyzer
            analyzer = get_analyzer()

        # Assert
        assert hasattr(analyzer, "analyze_website"), "analyze_website 메서드가 있어야 합니다."
        assert callable(analyzer.analyze_website)


class TestGetAnalyzerLlmBranch:
    """CLASSIFIER_MODE=llm (기본) 분기 테스트."""

    def test_classifier_mode_llm_returns_non_rule_analyzer(self) -> None:
        """CLASSIFIER_MODE=llm 이면 RuleAnalyzer가 아닌 분석기를 반환해야 한다."""
        # Arrange
        with patch.dict(os.environ, {"CLASSIFIER_MODE": "llm", "LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "fake-key"}):
            # Act
            from src.ai.analyzer import get_analyzer
            from src.rule.analyzer import RuleAnalyzer
            analyzer = get_analyzer()

        # Assert
        assert not isinstance(analyzer, RuleAnalyzer), "llm 모드에서는 RuleAnalyzer가 아니어야 합니다."

    def test_classifier_mode_unset_uses_llm_branch(self) -> None:
        """CLASSIFIER_MODE 미설정 시 RuleAnalyzer가 아닌 LLM 분석기를 반환해야 한다."""
        # Arrange
        env = {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "fake-key"}
        with patch.dict(os.environ, env):
            os.environ.pop("CLASSIFIER_MODE", None)

            # Act
            from src.ai.analyzer import get_analyzer
            from src.rule.analyzer import RuleAnalyzer
            analyzer = get_analyzer()

        # Assert
        assert not isinstance(analyzer, RuleAnalyzer), "미설정 시 LLM 분기여야 합니다."


class TestGetAnalyzerRuleAnalyzerBehavior:
    """RuleAnalyzer의 analyze_website 동작 검증 (run_quality_pipeline mock)."""

    def test_rule_analyzer_analyze_website_calls_pipeline(self) -> None:
        """RuleAnalyzer.analyze_website가 run_quality_pipeline을 호출해야 한다."""
        # Arrange
        mock_result = MagicMock()
        mock_result.extracted = {
            "ai_scope": {"scope_decision": "ai", "confidence": 0.9},
            "taxonomy": {
                "taxonomy_skipped": False,
                "primary_category": "Coding",
                "one_line_summary": "AI coding assistant",
                "sub_tasks": ["코드 생성"],
            },
            "homepage_title": "TestTool",
        }
        mock_result.total_score = 80.0
        mock_result.criteria = {}
        mock_result.normalized_url = "https://example.com"
        mock_result.input_url = "https://example.com"

        with patch("src.rule.analyzer.run_quality_pipeline", return_value=mock_result) as mock_pipeline:
            from src.rule.analyzer import RuleAnalyzer
            analyzer = RuleAnalyzer()

            # Act
            result = analyzer.analyze_website("https://example.com")

        # Assert
        mock_pipeline.assert_called_once_with("https://example.com")
        assert result["analyzer"] == "rule"

    def test_rule_analyzer_propagates_exceptions(self) -> None:
        """RuleAnalyzer.analyze_website는 파이프라인 예외를 그대로 전파해야 한다."""
        # Arrange
        with patch("src.rule.analyzer.run_quality_pipeline", side_effect=RuntimeError("파이프라인 오류")):
            from src.rule.analyzer import RuleAnalyzer
            analyzer = RuleAnalyzer()

            # Act / Assert
            with pytest.raises(RuntimeError, match="파이프라인 오류"):
                analyzer.analyze_website("https://example.com")

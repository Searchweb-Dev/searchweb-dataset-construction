"""
기능 5: get_classifier_mode 환경변수 헬퍼 테스트.

4가지 입력 케이스(미설정/rule/대소문자/잘못된값)를 각각 독립 테스트로 검증한다.
"""

from __future__ import annotations

import logging
import os
from unittest.mock import patch

import pytest

from src.core.config import get_classifier_mode


class TestGetClassifierModeDefault:
    """CLASSIFIER_MODE 미설정 케이스."""

    def test_unset_env_returns_llm(self) -> None:
        """CLASSIFIER_MODE 미설정 시 'llm'을 반환해야 한다."""
        # Arrange / Act
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLASSIFIER_MODE", None)
            result = get_classifier_mode()

        # Assert
        assert result == "llm"


class TestGetClassifierModeRule:
    """CLASSIFIER_MODE=rule 케이스."""

    def test_rule_returns_rule(self) -> None:
        """CLASSIFIER_MODE=rule 이면 'rule'을 반환해야 한다."""
        # Arrange / Act
        with patch.dict(os.environ, {"CLASSIFIER_MODE": "rule"}):
            result = get_classifier_mode()

        # Assert
        assert result == "rule"

    def test_llm_returns_llm(self) -> None:
        """CLASSIFIER_MODE=llm 이면 'llm'을 반환해야 한다."""
        # Arrange / Act
        with patch.dict(os.environ, {"CLASSIFIER_MODE": "llm"}):
            result = get_classifier_mode()

        # Assert
        assert result == "llm"


class TestGetClassifierModeCaseNormalization:
    """대소문자 정규화 케이스."""

    def test_uppercase_llm_returns_llm(self) -> None:
        """CLASSIFIER_MODE=LLM 이면 소문자 정규화 후 'llm'을 반환해야 한다."""
        # Arrange / Act
        with patch.dict(os.environ, {"CLASSIFIER_MODE": "LLM"}):
            result = get_classifier_mode()

        # Assert
        assert result == "llm"

    def test_uppercase_rule_returns_rule(self) -> None:
        """CLASSIFIER_MODE=RULE 이면 소문자 정규화 후 'rule'을 반환해야 한다."""
        # Arrange / Act
        with patch.dict(os.environ, {"CLASSIFIER_MODE": "RULE"}):
            result = get_classifier_mode()

        # Assert
        assert result == "rule"

    def test_mixedcase_rule_returns_rule(self) -> None:
        """CLASSIFIER_MODE=Rule 이면 소문자 정규화 후 'rule'을 반환해야 한다."""
        # Arrange / Act
        with patch.dict(os.environ, {"CLASSIFIER_MODE": "Rule"}):
            result = get_classifier_mode()

        # Assert
        assert result == "rule"


class TestGetClassifierModeInvalidValue:
    """잘못된 값 케이스."""

    def test_invalid_value_returns_llm_with_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """CLASSIFIER_MODE=invalid 이면 'llm'을 반환하고 경고 로그를 출력해야 한다."""
        # Arrange / Act
        with patch.dict(os.environ, {"CLASSIFIER_MODE": "invalid"}):
            with caplog.at_level(logging.WARNING):
                result = get_classifier_mode()

        # Assert
        assert result == "llm"
        assert any("invalid" in record.message or "invalid" in str(record.message).lower()
                   for record in caplog.records), "경고 로그가 출력되어야 합니다."

    def test_empty_string_returns_llm(self, caplog: pytest.LogCaptureFixture) -> None:
        """CLASSIFIER_MODE='' (빈 문자열) 이면 'llm'을 반환해야 한다."""
        # Arrange / Act
        with patch.dict(os.environ, {"CLASSIFIER_MODE": ""}):
            with caplog.at_level(logging.WARNING):
                result = get_classifier_mode()

        # Assert
        assert result == "llm"

    def test_random_value_returns_llm(self, caplog: pytest.LogCaptureFixture) -> None:
        """CLASSIFIER_MODE=gpt 같은 임의 값이면 'llm'을 반환해야 한다."""
        # Arrange / Act
        with patch.dict(os.environ, {"CLASSIFIER_MODE": "gpt"}):
            with caplog.at_level(logging.WARNING):
                result = get_classifier_mode()

        # Assert
        assert result == "llm"

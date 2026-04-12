"""AI scope classifier regression tests."""

from __future__ import annotations

import sys
from pathlib import Path
import unittest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from classifiers.ai_scope_classifier import AiScopeClassifierMixin  # noqa: E402
from config import EvalConfig  # noqa: E402
from models import FetchResult  # noqa: E402


class _DummyAiScopeEvaluator(AiScopeClassifierMixin):
    def __init__(self) -> None:
        self.config = EvalConfig()


def _homepage(url: str) -> FetchResult:
    return FetchResult(
        url=url,
        final_url=url,
        status_code=200,
        ok=True,
        html="",
        text="",
        title="",
        meta_description="",
        links=[],
    )


class TestAiScopeClassifier(unittest.TestCase):
    def test_boundary_case_returns_uncertain(self) -> None:
        evaluator = _DummyAiScopeEvaluator()
        text_blob = "gpt ai agent prompts checkout community shopping forum"
        result = evaluator._infer_ai_site_scope(text_blob, _homepage("https://chatgpt.com/"))

        self.assertTrue(result["is_ai_site"])
        self.assertEqual(result["scope_decision"], "uncertain")
        self.assertGreaterEqual(result["ai_signal_score"], 5)
        self.assertEqual(result["non_ai_signal_score"], 5)
        self.assertGreaterEqual(result["ai_non_ai_margin"], -1)
        self.assertLessEqual(result["ai_non_ai_margin"], 2)

    def test_known_brand_hint_can_promote_ai_scope(self) -> None:
        evaluator = _DummyAiScopeEvaluator()
        text_blob = "product page overview and support center"
        result = evaluator._infer_ai_site_scope(text_blob, _homepage("https://openai.com/"))

        self.assertTrue(result["is_ai_site"])
        self.assertEqual(result["scope_decision"], "ai")
        self.assertIn("브랜드", result["reason"])


if __name__ == "__main__":
    unittest.main()

"""Status policy regression tests."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from classifiers.status_policy import StatusPolicyMixin  # noqa: E402
from models import CriterionResult, FetchResult  # noqa: E402


class _DummyPolicyEvaluator(StatusPolicyMixin):
    def __init__(self) -> None:
        self.config = SimpleNamespace(
            use_playwright=True,
            min_text_len_for_static_success=700,
            min_links_for_static_success=8,
        )


class TestStatusPolicy(unittest.TestCase):
    def test_review_gate_for_uncertain_scope_and_thin_requests_result(self) -> None:
        evaluator = _DummyPolicyEvaluator()
        criteria = {
            "usable_now": CriterionResult("usable_now", True, "ok", 0.95),
            "clear_function_desc": CriterionResult("clear_function_desc", True, "ok", 0.9),
            "has_pricing": CriterionResult("has_pricing", True, "ok", 0.95),
            "has_docs_or_help": CriterionResult("has_docs_or_help", True, "ok", 0.9),
            "has_privacy_or_data_policy": CriterionResult("has_privacy_or_data_policy", True, "ok", 0.95),
        }
        homepage = FetchResult(
            url="https://example.com/",
            final_url="https://example.com/",
            status_code=200,
            ok=True,
            html="",
            text="thin text",
            title="Example",
            meta_description="",
            links=[],
            fetched_by="requests",
        )
        extracted = {
            "ai_scope": {"scope_decision": "uncertain"},
            "contact_sales_only": False,
            "faq_only_docs": False,
            "anti_bot_blocked": False,
            "playwright_enabled": True,
        }

        review_required, reasons = evaluator._review_gate(criteria, homepage, extracted, "curated")
        self.assertTrue(review_required)
        self.assertIn("AI 사이트 판정이 경계 구간(uncertain)으로 수동 확인이 필요함", reasons)
        self.assertIn("Playwright 재수집 없이 requests 결과만 사용됨", reasons)


if __name__ == "__main__":
    unittest.main()


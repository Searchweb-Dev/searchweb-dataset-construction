"""Pipeline management snapshot and registry tests."""

from __future__ import annotations

import sys
import types
from pathlib import Path
import unittest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if "bs4" not in sys.modules:
    bs4_stub = types.ModuleType("bs4")

    class _BeautifulSoupStub:  # pragma: no cover - import-only test stub
        def __init__(self, *_args, **_kwargs) -> None:
            pass

    bs4_stub.BeautifulSoup = _BeautifulSoupStub
    sys.modules["bs4"] = bs4_stub

from config import EvalConfig  # noqa: E402
from models import EvaluationResult  # noqa: E402
from pipeline import _annotate_results_with_management, _parse_cli_args  # noqa: E402


def _result(
    *,
    final_status: str,
    review_required: bool,
    review_reasons: list[str],
    anti_bot_blocked: bool,
    ai_scope_decision: str,
    taxonomy_confidence: float,
    total_score: float,
) -> EvaluationResult:
    return EvaluationResult(
        input_url="https://example.com",
        normalized_url="https://example.com/",
        predicted_status=final_status,
        final_status=final_status,
        passed_count=4,
        hard_pass=True,
        review_required=review_required,
        review_reasons=review_reasons,
        criteria={},
        summary="",
        extracted={
            "homepage_final_url": "https://example.com/",
            "homepage_title": "Example AI - Home",
            "anti_bot_blocked": anti_bot_blocked,
            "ai_scope": {"scope_decision": ai_scope_decision},
            "taxonomy": {
                "primary_category": "Coding",
                "primary_confidence": taxonomy_confidence,
                "taxonomy_skipped": False,
            },
        },
        total_score=total_score,
        score_breakdown={},
    )


class TestPipelineManagement(unittest.TestCase):
    def test_parse_cli_args_supports_source_and_registry(self) -> None:
        urls, output_json, registry_json, source = _parse_cli_args(
            [
                "--source",
                "ai-tools.json",
                "--registry-json",
                "result/tools.json",
                "--output-json",
                "result/run.json",
                "https://a.com",
                "https://a.com",
                "https://b.com",
            ]
        )
        self.assertEqual(urls, ["https://a.com", "https://b.com"])
        self.assertEqual(output_json, "result/run.json")
        self.assertEqual(registry_json, "result/tools.json")
        self.assertEqual(source, "ai-tools.json")

    def test_parse_cli_args_can_disable_registry(self) -> None:
        urls, _, registry_json, _ = _parse_cli_args(
            [
                "--registry-json",
                "none",
                "https://example.com",
            ]
        )
        self.assertEqual(urls, ["https://example.com"])
        self.assertEqual(registry_json, "")

    def test_annotate_results_with_management_updates_registry_history(self) -> None:
        config = EvalConfig()
        registry: dict[str, dict[str, object]] = {}

        first = _result(
            final_status="incubating",
            review_required=True,
            review_reasons=["manual_review_needed"],
            anti_bot_blocked=False,
            ai_scope_decision="uncertain",
            taxonomy_confidence=0.45,
            total_score=82.4,
        )
        _annotate_results_with_management(
            results=[first],
            source="ai-tools.json",
            checked_at="2026-04-12T10:00:00Z",
            registry_tools=registry,
            config=config,
        )

        self.assertIsNotNone(first.management)
        assert first.management is not None
        self.assertEqual(first.management["source"], "ai-tools.json")
        self.assertEqual(first.management["lifecycle_state"], "incubating")
        self.assertIn("ai_scope_uncertain", first.management["review_queue_reasons"])
        self.assertIn("review_required", first.management["review_queue_reasons"])
        self.assertIn("low_taxonomy_confidence", first.management["review_queue_reasons"])
        self.assertEqual(first.management["reevaluation_priority"], "fast")

        tool_id = str(first.management["tool_id"])
        self.assertIn(tool_id, registry)
        self.assertEqual(registry[tool_id]["first_seen_at"], "2026-04-12T10:00:00Z")
        self.assertEqual(len(registry[tool_id]["change_history"]), 1)
        self.assertEqual(registry[tool_id]["change_history"][0]["changed_fields"], ["new_tool"])

        second = _result(
            final_status="rejected",
            review_required=False,
            review_reasons=[],
            anti_bot_blocked=True,
            ai_scope_decision="ai",
            taxonomy_confidence=0.90,
            total_score=41.0,
        )
        _annotate_results_with_management(
            results=[second],
            source="ai-tools.json",
            checked_at="2026-04-13T10:00:00Z",
            registry_tools=registry,
            config=config,
        )

        assert second.management is not None
        self.assertEqual(second.management["first_seen_at"], "2026-04-12T10:00:00Z")
        self.assertIn("status_changed:incubating->rejected", second.management["review_queue_reasons"])
        self.assertIn("anti_bot_blocked", second.management["review_queue_reasons"])
        self.assertEqual(second.management["reevaluation_priority"], "retry_short_backoff")
        self.assertEqual(len(registry[tool_id]["change_history"]), 2)


if __name__ == "__main__":
    unittest.main()

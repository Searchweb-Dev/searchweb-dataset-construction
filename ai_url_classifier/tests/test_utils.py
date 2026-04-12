"""Utility-level regression tests."""

from __future__ import annotations

import sys
from pathlib import Path
import unittest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils import likely_related_external_candidates  # noqa: E402


class TestLikelyRelatedExternalCandidates(unittest.TestCase):
    def test_openai_family_seed_urls_for_chatgpt(self) -> None:
        candidates = likely_related_external_candidates("https://chatgpt.com/")
        self.assertEqual(
            candidates,
            [
                "https://chatgpt.com/pricing",
                "https://help.openai.com/en",
                "https://openai.com/policies/row-privacy-policy",
            ],
        )

    def test_non_openai_domain_has_no_seed_urls(self) -> None:
        candidates = likely_related_external_candidates("https://example.com/")
        self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()


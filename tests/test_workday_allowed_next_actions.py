from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from offerops.adapters import plan_adapter
from offerops.adapters.base import AdapterContext
from offerops.adapters.workday import WorkdayAdapter
from offerops.models import ParserResult, WorkdayStageDetection
from offerops.parser import parse_job_page

FIXTURES = Path(__file__).parent / "fixtures"
WORKDAY_URL = "https://example.wd5.myworkdayjobs.com/job/example"


class WorkdayAllowedNextActionsTests(unittest.TestCase):
    def test_known_non_review_stages_allow_read_only_preview_and_human_review(
        self,
    ) -> None:
        cases = [
            "workday_stage_account_gate.html",
            "workday_stage_my_information.html",
            "workday_stage_my_experience.html",
            "workday_stage_application_questions.html",
            "workday_stage_voluntary_disclosures.html",
        ]

        for fixture_name in cases:
            with self.subTest(fixture_name=fixture_name):
                html = _fixture(fixture_name)
                parser_result = parse_job_page(WORKDAY_URL, html)

                payload = plan_adapter(parser_result, html).to_dict()
                details = payload["details"]
                self.assertIsInstance(details, dict)
                self.assertEqual(
                    details["allowed_next_actions"],
                    ["preview_current_stage", "human_review"],
                )

    def test_review_stage_allows_only_human_review_and_never_submit(self) -> None:
        html = _fixture("workday_stage_review.html")
        parser_result = parse_job_page(WORKDAY_URL, html)

        payload = plan_adapter(parser_result, html).to_dict()
        details = payload["details"]
        self.assertIsInstance(details, dict)

        self.assertEqual(details["stage"], "review")
        self.assertEqual(details["allowed_next_actions"], ["human_review"])
        self.assertNotIn("submit", " ".join(details["allowed_next_actions"]))

    def test_unknown_stage_allows_only_human_review(self) -> None:
        html = _fixture("workday_stage_unknown.html")
        parser_result = parse_job_page(WORKDAY_URL, html)

        payload = plan_adapter(parser_result, html).to_dict()
        details = payload["details"]
        self.assertIsInstance(details, dict)

        self.assertEqual(payload["status"], "manual_review_required")
        self.assertEqual(details["stage"], "unknown")
        self.assertEqual(details["allowed_next_actions"], ["human_review"])

    def test_low_confidence_stage_allows_only_human_review(self) -> None:
        parser_result = ParserResult(
            provider="workday",
            adapter="workday_adapter",
            reason="host:myworkdayjobs.com",
        )

        with patch(
            "offerops.adapters.workday.detect_workday_stage",
            return_value=WorkdayStageDetection(
                stage="my_information",
                confidence=0.65,
                reason="matched:my_information:low_confidence",
            ),
        ):
            payload = WorkdayAdapter().plan(
                AdapterContext(parser_result=parser_result, html="<main />")
            ).to_dict()

        details = payload["details"]
        self.assertIsInstance(details, dict)
        self.assertEqual(payload["status"], "manual_review_required")
        self.assertEqual(details["stage"], "my_information")
        self.assertEqual(details["allowed_next_actions"], ["human_review"])

    def test_cli_plan_outputs_allowed_next_actions(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "offerops",
                "plan",
                WORKDAY_URL,
                "--html-file",
                str(FIXTURES / "workday_stage_my_information.html"),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["details"]["allowed_next_actions"],
            ["preview_current_stage", "human_review"],
        )


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

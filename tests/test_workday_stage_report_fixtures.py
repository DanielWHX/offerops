from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

FIXTURES = Path(__file__).parent / "fixtures"
WORKDAY_URL = "https://example.wd5.myworkdayjobs.com/job/example"


class WorkdayStageReportFixtureTests(unittest.TestCase):
    def test_cli_plan_matches_stage_report_fixtures(self) -> None:
        cases = [
            "account_gate",
            "my_information",
            "my_experience",
            "application_questions",
            "voluntary_disclosures",
            "review",
            "unknown",
        ]

        for stage in cases:
            with self.subTest(stage=stage):
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "offerops",
                        "plan",
                        WORKDAY_URL,
                        "--html-file",
                        str(FIXTURES / f"workday_stage_{stage}.html"),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                expected = _json_fixture(f"workday_stage_report_{stage}.json")
                self.assertEqual(json.loads(completed.stdout), expected)


def _json_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

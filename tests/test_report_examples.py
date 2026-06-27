from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs" / "examples" / "reports"


class ReportExampleTests(unittest.TestCase):
    def test_report_examples_match_current_cli_output(self) -> None:
        cases = [
            (
                "greenhouse_plan_report.json",
                [
                    "plan",
                    "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582",
                    "--html-file",
                    "tests/fixtures/greenhouse_application.html",
                    "--profile-file",
                    "tests/fixtures/applicant_profile.json",
                ],
            ),
            (
                "lever_plan_report.json",
                [
                    "plan",
                    "https://jobs.lever.co/example-company/example-role",
                    "--html-file",
                    "tests/fixtures/lever.html",
                ],
            ),
            (
                "workday_stage_plan_report.json",
                [
                    "plan",
                    "https://example.wd5.myworkdayjobs.com/job/example",
                    "--html-file",
                    "tests/fixtures/workday_stage_my_information.html",
                ],
            ),
            (
                "unknown_plan_report.json",
                [
                    "plan",
                    "https://example.com/jobs/123",
                    "--html-file",
                    "tests/fixtures/unknown.html",
                ],
            ),
        ]

        for example_name, command_args in cases:
            with self.subTest(example=example_name):
                self.assertEqual(
                    _run_offerops(command_args),
                    _json_example(example_name),
                )


def _run_offerops(command_args: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-m", "offerops", *command_args],
        check=True,
        capture_output=True,
        cwd=ROOT,
        text=True,
    )
    return json.loads(completed.stdout)


def _json_example(name: str) -> dict[str, object]:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

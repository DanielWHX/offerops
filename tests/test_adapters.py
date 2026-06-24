from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from offerops import cli
from offerops.adapters import get_adapter, plan_adapter
from offerops.adapters.ashby import AshbyAdapter
from offerops.adapters.greenhouse import GreenhouseAdapter
from offerops.adapters.lever import LeverAdapter
from offerops.adapters.oracle_cloud_hcm import OracleCloudHCMAdapter
from offerops.adapters.unknown import UnknownAdapter
from offerops.adapters.workday import WorkdayAdapter
from offerops.models import ParserResult
from offerops.parser import detect_provider, parse_job_page

FIXTURES = Path(__file__).parent / "fixtures"


class AdapterRegistryTests(unittest.TestCase):
    def test_routes_known_adapter_names(self) -> None:
        cases = {
            "workday_adapter": WorkdayAdapter,
            "greenhouse_adapter": GreenhouseAdapter,
            "lever_adapter": LeverAdapter,
            "ashby_adapter": AshbyAdapter,
            "oracle_cloud_hcm_adapter": OracleCloudHCMAdapter,
        }

        for adapter_name, adapter_type in cases.items():
            with self.subTest(adapter_name=adapter_name):
                self.assertIsInstance(get_adapter(adapter_name), adapter_type)

    def test_unknown_adapter_name_routes_to_manual_review_adapter(self) -> None:
        self.assertIsInstance(get_adapter("missing_adapter"), UnknownAdapter)

    def test_detected_providers_route_to_registered_adapters(self) -> None:
        cases = {
            "https://example.wd5.myworkdayjobs.com/job/example": WorkdayAdapter,
            "https://boards.greenhouse.io/example/jobs/1": GreenhouseAdapter,
            "https://jobs.lever.co/example/job-1": LeverAdapter,
            "https://jobs.ashbyhq.com/example/job-1": AshbyAdapter,
            "https://example.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/1": OracleCloudHCMAdapter,
        }

        for url, adapter_type in cases.items():
            with self.subTest(url=url):
                detection = detect_provider(url)
                self.assertIsInstance(get_adapter(detection.adapter), adapter_type)

    def test_known_adapter_plan_is_non_executing_skeleton(self) -> None:
        result = ParserResult(
            provider="workday",
            adapter="workday_adapter",
            reason="host:myworkdayjobs.com",
        )

        adapter_result = plan_adapter(result)

        self.assertEqual(adapter_result.provider, "workday")
        self.assertEqual(adapter_result.adapter, "workday_adapter")
        self.assertEqual(adapter_result.status, "not_implemented")

    def test_unknown_adapter_requires_manual_review(self) -> None:
        result = ParserResult(
            provider="unknown",
            adapter="unknown_adapter",
            reason="no_known_provider_signature",
        )

        adapter_result = plan_adapter(result)

        self.assertEqual(adapter_result.provider, "unknown")
        self.assertEqual(adapter_result.adapter, "unknown_adapter")
        self.assertEqual(adapter_result.status, "manual_review_required")

    def test_greenhouse_adapter_preflights_application_fields(self) -> None:
        html = _fixture("greenhouse_application.html")
        parser_result = parse_job_page(
            "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582",
            html,
        )

        adapter_result = plan_adapter(parser_result, html)
        payload = adapter_result.to_dict()

        self.assertEqual(payload["provider"], "greenhouse")
        self.assertEqual(payload["adapter"], "greenhouse_adapter")
        self.assertEqual(payload["status"], "planned")
        details = payload["details"]
        self.assertIsInstance(details, dict)
        self.assertEqual(details["field_count"], 5)
        self.assertEqual(
            [field["field_key"] for field in details["fields"]],
            ["first_name", "last_name", "email", "phone", "resume"],
        )
        self.assertEqual(details["review_reasons"], ["final_submit_boundary"])

    def test_cli_plan_outputs_known_provider_adapter_result(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "offerops",
                "plan",
                "https://boards.greenhouse.io/example/jobs/1",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["provider"], "greenhouse")
        self.assertEqual(payload["adapter"], "greenhouse_adapter")
        self.assertEqual(payload["status"], "not_implemented")

    def test_cli_plan_outputs_unknown_manual_review_result(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "offerops",
                "plan",
                "https://example.com/jobs/123",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["provider"], "unknown")
        self.assertEqual(payload["adapter"], "unknown_adapter")
        self.assertEqual(payload["status"], "manual_review_required")

    def test_cli_demo_outputs_live_planning_report_shape(self) -> None:
        stdout = StringIO()
        html = """
        <script type="application/ld+json">
          {
            "@type": "JobPosting",
            "title": "Security Engineering Intern",
            "hiringOrganization": {"name": "Bugcrowd"},
            "jobLocation": "Remote, USA"
          }
        </script>
        """

        with patch("offerops.cli._fetch_url_html", return_value=html) as fetch:
            with redirect_stdout(stdout):
                exit_code = cli.main(
                    [
                        "demo",
                        "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582",
                    ]
                )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        fetch.assert_called_once_with(
            "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582",
            15.0,
        )
        self.assertEqual(payload["parser_result"]["provider"], "greenhouse")
        self.assertEqual(
            payload["parser_result"]["job_title"],
            "Security Engineering Intern",
        )
        self.assertEqual(payload["adapter_result"]["status"], "not_implemented")
        self.assertEqual(payload["safety"]["browser_automation"], "not_used")
        self.assertEqual(payload["safety"]["final_submit"], "not_allowed")

    def test_cli_demo_outputs_unknown_manual_review_report(self) -> None:
        stdout = StringIO()

        with patch(
            "offerops.cli._fetch_url_html",
            return_value="<title>Example Jobs</title>",
        ):
            with redirect_stdout(stdout):
                exit_code = cli.main(["demo", "https://example.com/jobs/123"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["parser_result"]["provider"], "unknown")
        self.assertEqual(payload["adapter_result"]["status"], "manual_review_required")

    def test_cli_demo_reports_fetch_failure(self) -> None:
        stderr = StringIO()

        with patch("offerops.cli._fetch_url_html", side_effect=OSError("network down")):
            with redirect_stderr(stderr):
                exit_code = cli.main(["demo", "https://example.com/jobs/123"])

        payload = json.loads(stderr.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["error"], "fetch_failed")
        self.assertEqual(payload["url"], "https://example.com/jobs/123")


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

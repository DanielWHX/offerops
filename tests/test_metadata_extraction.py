from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from offerops.parser import parse_job_page

FIXTURES = Path(__file__).parent / "fixtures"


class MetadataExtractionTests(unittest.TestCase):
    def test_extracts_workday_metadata_from_saved_html(self) -> None:
        result = parse_job_page(
            "https://generac.wd5.myworkdayjobs.com/en-US/external/job/example",
            _fixture("workday.html"),
        )

        self.assertEqual(result.provider, "workday")
        self.assertEqual(result.adapter, "workday_adapter")
        self.assertEqual(result.job_title, "Computer Engineering Intern")
        self.assertEqual(result.company, "Generac")
        self.assertEqual(result.location, "Pewaukee, WI, USA")

    def test_extracts_greenhouse_metadata_from_saved_html(self) -> None:
        result = parse_job_page(
            "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582",
            _fixture("greenhouse.html"),
        )

        self.assertEqual(result.provider, "greenhouse")
        self.assertEqual(result.adapter, "greenhouse_adapter")
        self.assertEqual(result.job_title, "Security Engineering Intern")
        self.assertEqual(result.company, "Bugcrowd")
        self.assertEqual(result.location, "Remote, USA")

    def test_extracts_ashby_metadata_from_saved_html(self) -> None:
        result = parse_job_page(
            "https://jobs.ashbyhq.com/gen-digital/example/application",
            _fixture("ashby.html"),
        )

        self.assertEqual(result.provider, "ashby")
        self.assertEqual(result.adapter, "ashby_adapter")
        self.assertEqual(result.job_title, "Software Engineering Intern")
        self.assertEqual(result.company, "Gen Digital")
        self.assertEqual(result.location, "Tempe, AZ")

    def test_extracts_oracle_cloud_hcm_metadata_from_saved_html(self) -> None:
        result = parse_job_page(
            "https://ebwg.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/19501",
            _fixture("oracle_cloud_hcm.html"),
        )

        self.assertEqual(result.provider, "oracle_cloud_hcm")
        self.assertEqual(result.adapter, "oracle_cloud_hcm_adapter")
        self.assertEqual(result.job_title, "Software Engineer Intern")
        self.assertEqual(result.company, "Oracle")
        self.assertEqual(result.location, "Austin, TX")

    def test_unknown_returns_null_metadata_even_with_saved_html(self) -> None:
        result = parse_job_page("https://example.com/jobs/123", _fixture("unknown.html"))

        self.assertEqual(result.provider, "unknown")
        self.assertEqual(result.adapter, "unknown_adapter")
        self.assertIsNone(result.job_title)
        self.assertIsNone(result.company)
        self.assertIsNone(result.location)

    def test_cli_accepts_html_file(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "offerops",
                "parse",
                "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582",
                "--html-file",
                str(FIXTURES / "greenhouse.html"),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["provider"], "greenhouse")
        self.assertEqual(payload["job_title"], "Security Engineering Intern")
        self.assertEqual(payload["company"], "Bugcrowd")
        self.assertEqual(payload["location"], "Remote, USA")


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import subprocess
import sys
import unittest

from offerops.parser import detect_provider

WORKDAY_URL = (
    "https://generac.wd5.myworkdayjobs.com/en-US/external/job/"
    "Pewaukee-WI---USA/Computer-Engineering-Intern_JR14798"
    "?utm_source=Simplify&ref=Simplify"
)
ORACLE_CLOUD_HCM_URL = (
    "https://ebwg.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/"
    "en/sites/CX/job/19501?utm_source=Simplify&ref=Simplify"
)
ASHBY_URL = (
    "https://jobs.ashbyhq.com/gen-digital/"
    "0818d1f1-e3c0-4a8a-afb8-72dd1265a13d/application"
    "?utm_source=Simplify&ref=Simplify"
)
GREENHOUSE_URL = (
    "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582"
    "?utm_source=Simplify&ref=Simplify"
)


class ProviderDetectionTests(unittest.TestCase):
    def test_detects_workday_from_real_url(self) -> None:
        result = detect_provider(WORKDAY_URL)

        self.assertEqual(result.provider, "workday")
        self.assertEqual(result.adapter, "workday_adapter")

    def test_detects_oracle_cloud_hcm_from_real_url(self) -> None:
        result = detect_provider(ORACLE_CLOUD_HCM_URL)

        self.assertEqual(result.provider, "oracle_cloud_hcm")
        self.assertEqual(result.adapter, "oracle_cloud_hcm_adapter")

    def test_detects_ashby_from_real_url(self) -> None:
        result = detect_provider(ASHBY_URL)

        self.assertEqual(result.provider, "ashby")
        self.assertEqual(result.adapter, "ashby_adapter")

    def test_detects_greenhouse_from_real_url(self) -> None:
        result = detect_provider(GREENHOUSE_URL)

        self.assertEqual(result.provider, "greenhouse")
        self.assertEqual(result.adapter, "greenhouse_adapter")

    def test_detects_lever_from_domain_signature(self) -> None:
        result = detect_provider("https://jobs.lever.co/example-company/example-role")

        self.assertEqual(result.provider, "lever")
        self.assertEqual(result.adapter, "lever_adapter")

    def test_unknown_fallback(self) -> None:
        result = detect_provider("https://example.com/jobs/123")

        self.assertEqual(result.provider, "unknown")
        self.assertEqual(result.adapter, "unknown_adapter")

    def test_cli_outputs_provider_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "offerops",
                "parse",
                "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["provider"], "greenhouse")
        self.assertEqual(payload["adapter"], "greenhouse_adapter")


if __name__ == "__main__":
    unittest.main()

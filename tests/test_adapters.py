from __future__ import annotations

import json
import subprocess
import sys
import unittest

from offerops.adapters import get_adapter, plan_adapter
from offerops.adapters.ashby import AshbyAdapter
from offerops.adapters.greenhouse import GreenhouseAdapter
from offerops.adapters.lever import LeverAdapter
from offerops.adapters.oracle_cloud_hcm import OracleCloudHCMAdapter
from offerops.adapters.unknown import UnknownAdapter
from offerops.adapters.workday import WorkdayAdapter
from offerops.models import ParserResult
from offerops.parser import detect_provider


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


if __name__ == "__main__":
    unittest.main()

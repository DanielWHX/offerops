from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "browser_demo_router.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("browser_demo_router", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load browser demo router script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BrowserDemoRouterTests(unittest.TestCase):
    def test_routes_greenhouse_to_greenhouse_demo(self) -> None:
        script = _load_script_module()

        route = script.build_route(
            "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582"
        )

        self.assertEqual(route["provider"], "greenhouse")
        self.assertEqual(route["status"], "routed")
        self.assertEqual(route["script"], "scripts/run_greenhouse_demo.sh")
        self.assertEqual(
            route["safety"]["final_submit"], "blocked_by_provider_demo_guard"
        )

    def test_routes_lever_to_lever_demo(self) -> None:
        script = _load_script_module()

        route = script.build_route(
            "https://jobs.lever.co/field-ai/example/apply"
        )

        self.assertEqual(route["provider"], "lever")
        self.assertEqual(route["status"], "routed")
        self.assertEqual(route["script"], "scripts/run_lever_demo.sh")

    def test_unsupported_known_providers_return_manual_review(self) -> None:
        script = _load_script_module()
        cases = [
            (
                "https://example.wd5.myworkdayjobs.com/en-US/external/job/example",
                "workday",
            ),
            ("https://jobs.ashbyhq.com/example/example-role", "ashby"),
            (
                "https://example.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/123",
                "oracle_cloud_hcm",
            ),
        ]

        for url, provider in cases:
            with self.subTest(provider=provider):
                route = script.build_route(url)

                self.assertEqual(route["provider"], provider)
                self.assertEqual(route["status"], "manual_review")
                self.assertEqual(route["command"], [])
                self.assertEqual(route["safety"]["browser_control"], "not_started")

    def test_unknown_returns_unsupported_without_browser_command(self) -> None:
        script = _load_script_module()

        route = script.build_route("https://example.com/jobs/123")

        self.assertEqual(route["provider"], "unknown")
        self.assertEqual(route["status"], "unsupported")
        self.assertEqual(route["command"], [])

    def test_cli_dry_run_outputs_route_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "https://jobs.lever.co/example/example-role",
                "--dry-run",
            ],
            check=True,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(ROOT / "src")},
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["provider"], "lever")
        self.assertEqual(payload["status"], "routed")
        self.assertEqual(payload["script"], "scripts/run_lever_demo.sh")


if __name__ == "__main__":
    unittest.main()

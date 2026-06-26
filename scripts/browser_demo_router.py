from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from offerops.parser import detect_provider


SUPPORTED_ROUTES = {
    "greenhouse": "scripts/run_greenhouse_demo.sh",
    "lever": "scripts/run_lever_demo.sh",
}
MANUAL_REVIEW_PROVIDERS = {"workday", "ashby", "oracle_cloud_hcm"}


def main() -> int:
    args, demo_args = build_parser().parse_known_args()
    repo_root = Path(__file__).resolve().parents[1]
    route = build_route(args.url, repo_root)

    if route["status"] != "routed" or args.dry_run:
        print(json.dumps(route, indent=2, sort_keys=True), flush=True)
        return 0

    command = [str(repo_root / route["script"]), args.url, *demo_args]
    completed = subprocess.run(command, cwd=repo_root, check=False)
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Route one job URL to a supported OfferOps browser demo."
    )
    parser.add_argument("url", help="Job application URL")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the routing decision without launching a browser demo.",
    )
    return parser


def build_route(url: str, repo_root: Path | None = None) -> dict[str, Any]:
    detection = detect_provider(url)
    base: dict[str, Any] = {
        "url": url,
        "provider": detection.provider,
        "adapter": detection.adapter,
        "reason": detection.reason,
        "supported_providers": sorted(SUPPORTED_ROUTES),
    }

    script = SUPPORTED_ROUTES.get(detection.provider)
    if script:
        command = [script, url]
        if repo_root is not None:
            command[0] = str(repo_root / script)
        return {
            **base,
            "status": "routed",
            "script": script,
            "command": command,
            "safety": {
                "browser_control": "delegated_to_provider_demo",
                "final_submit": "blocked_by_provider_demo_guard",
            },
        }

    status = (
        "manual_review"
        if detection.provider in MANUAL_REVIEW_PROVIDERS
        else "unsupported"
    )
    return {
        **base,
        "status": status,
        "script": None,
        "command": [],
        "safety": {
            "browser_control": "not_started",
            "final_submit": "not_reached",
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())

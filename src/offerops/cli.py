from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .adapters import plan_adapter
from .parser import parse_job_page


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="offerops")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse = subparsers.add_parser("parse", help="Detect the ATS provider for one job URL.")
    parse.add_argument("url", help="Job application URL")
    parse.add_argument("--html-file", help="Saved HTML file used for metadata extraction")

    plan = subparsers.add_parser("plan", help="Plan the adapter action for one job URL.")
    plan.add_argument("url", help="Job application URL")
    plan.add_argument("--html-file", help="Saved HTML file used for metadata extraction")
    plan.add_argument("--profile-file", help="Fake applicant profile JSON for fill preview")

    demo = subparsers.add_parser("demo", help="Fetch one job page and print a planning report.")
    demo.add_argument("url", help="Job application URL")
    demo.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout in seconds")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "parse":
        html = _read_html_file(args.html_file)
        result = parse_job_page(args.url, html)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "plan":
        html = _read_html_file(args.html_file)
        applicant_profile = _read_profile_file(args.profile_file)
        result = parse_job_page(args.url, html)
        adapter_result = plan_adapter(result, html, applicant_profile)
        print(json.dumps(adapter_result.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "demo":
        try:
            html = _fetch_url_html(args.url, args.timeout)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            error = {
                "error": "fetch_failed",
                "message": str(exc),
                "url": args.url,
            }
            print(json.dumps(error, indent=2, sort_keys=True), file=sys.stderr)
            return 1

        parser_result = parse_job_page(args.url, html)
        adapter_result = plan_adapter(parser_result, html)
        report = {
            "parser_result": parser_result.to_dict(),
            "adapter_result": adapter_result.to_dict(),
            "safety": {
                "browser_automation": "not_used",
                "final_submit": "not_allowed",
                "network": "http_get_only",
            },
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    return 2


def _read_html_file(path: str | None) -> str | None:
    return Path(path).read_text(encoding="utf-8") if path else None


def _read_profile_file(path: str | None) -> dict[str, str] | None:
    if not path:
        return None

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("profile file must contain a JSON object")

    return {
        key: value
        for key, value in payload.items()
        if isinstance(key, str) and isinstance(value, str)
    }


def _fetch_url_html(url: str, timeout: float) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "OfferOps/0.1",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")

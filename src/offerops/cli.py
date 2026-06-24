from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

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
        result = parse_job_page(args.url, html)
        adapter_result = plan_adapter(result, html)
        print(json.dumps(adapter_result.to_dict(), indent=2, sort_keys=True))
        return 0

    return 2


def _read_html_file(path: str | None) -> str | None:
    return Path(path).read_text(encoding="utf-8") if path else None

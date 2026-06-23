from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .parser import parse_job_page


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="offerops")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse = subparsers.add_parser("parse", help="Detect the ATS provider for one job URL.")
    parse.add_argument("url", help="Job application URL")
    parse.add_argument("--html-file", help="Saved HTML file used for metadata extraction")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "parse":
        html = Path(args.html_file).read_text(encoding="utf-8") if args.html_file else None
        result = parse_job_page(args.url, html)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0

    return 2

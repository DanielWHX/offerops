from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from .parser import detect_provider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="offerops")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse = subparsers.add_parser("parse", help="Detect the ATS provider for one job URL.")
    parse.add_argument("url", help="Job application URL")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "parse":
        result = detect_provider(args.url)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0

    return 2

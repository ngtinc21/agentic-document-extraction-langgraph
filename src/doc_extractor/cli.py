"""Command-line entrypoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .graph import run_workflow
from .io import write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a dictionary-driven extraction job.")
    parser.add_argument("--job", required=True, help="Path to an extraction job JSON file.")
    parser.add_argument("--out", default=None, help="Optional JSON output path.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_workflow(args.job)
    if args.out:
        write_json(Path(args.out), result)
        print(f"Wrote result to {args.out}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

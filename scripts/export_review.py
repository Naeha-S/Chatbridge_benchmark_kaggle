#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from continuitybench.review import export_review_file, summarize_review_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Export evaluator-only human review records")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary-output", required=True)
    args = parser.parse_args()
    cases = [json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    export_review_file(cases, args.output)
    summarize_review_file(args.output, args.summary_output)
    print(f"Review file -> {args.output}")
    print(f"Review summary -> {args.summary_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

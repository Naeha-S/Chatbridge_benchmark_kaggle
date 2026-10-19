#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from continuitybench.generator import generate_cases
from continuitybench.quality import coverage_report, split_dataset, validate_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic ContinuityBench synthetic dataset")
    parser.add_argument("--output", required=True, help="Path for JSONL output")
    parser.add_argument("--count", type=int, default=84, help="Number of cases")
    parser.add_argument("--seed", type=int, default=7, help="Random seed")
    parser.add_argument("--qa-output", default="reports/generated/qa_report.json", help="Path for QA report JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = generate_cases(args.count, seed=args.seed)
    qa = validate_dataset(cases)
    splits = split_dataset(cases, seed=args.seed)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    qa_path = Path(args.qa_output)
    qa_path.parent.mkdir(parents=True, exist_ok=True)
    qa_report = {
        "seed": args.seed,
        "count": args.count,
        "split_sizes": {name: len(items) for name, items in splits.items()},
        "coverage": coverage_report(cases),
        "validation": qa,
        "limitations": [
            "Synthetic templates may not reflect real conversational ambiguity.",
            "Semantic validity still requires human sample review.",
        ],
    }
    qa_path.write_text(json.dumps(qa_report, indent=2), encoding="utf-8")

    print(f"Generated {len(cases)} cases -> {output_path}")
    print(f"QA report -> {qa_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from collections import Counter
from pathlib import Path
from continuitybench.quality import split_dataset, validate_dataset

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"cb-\d{5}|case-\d{6}", "<id>", text)
    text = re.sub(r"\b\d+\b", "<num>", text)
    return re.sub(r"\s+", " ", text).strip()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cases = [json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    normalized = [normalize(" ".join(turn["content"] for turn in c["source_conversation"])) for c in cases]
    literal = [json.dumps(c["source_conversation"], sort_keys=True) for c in cases]
    templates = Counter(normalized)
    ngrams = Counter(" ".join(normalized[i].split()[j:j+4]) for i in range(len(normalized)) for j in range(max(0, len(normalized[i].split()) - 3)))
    splits = split_dataset(cases, seed=7)
    split_templates = {name: {normalize(" ".join(t["content"] for t in c["source_conversation"])) for c in group} for name, group in splits.items()}
    overlap = {f"{a}_vs_{b}": len(split_templates[a] & split_templates[b]) for a in split_templates for b in split_templates if a < b}
    report = {"normalization": "lowercase; replace CB-/CASE- identifiers and standalone numbers; collapse whitespace", "cases": len(cases), "literal_exact_duplicate_rate": ((len(cases)-len(set(literal))) / len(cases) if cases else 0), "normalized_exact_duplicate_rate": ((len(cases)-len(set(normalized))) / len(cases) if cases else 0), "unique_normalized_conversation_templates": len(set(normalized)), "conversation_length_counts": dict(Counter(len(c["source_conversation"]) for c in cases)), "task_pattern_counts": dict(Counter(normalize(c["handoff_task"]) for c in cases)), "constraint_pattern_counts": dict(Counter(" | ".join(sorted(normalize(x) for x in c["required_constraints"])) for c in cases)), "category_counts": dict(Counter(x for c in cases for x in c["failure_categories"])), "difficulty_counts": dict(Counter(c["difficulty_level"] for c in cases)), "combination_counts": dict(Counter("+".join(c["failure_categories"]) for c in cases)), "top_repeated_4grams": ngrams.most_common(20), "cross_split_normalized_template_overlap": overlap, "validation": validate_dataset(cases), "limitations": ["Lexical normalization is not semantic similarity.", "The report does not establish model shortcut performance.", "Human review is still required for semantic validity."]}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True); Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8"); print(f"Diversity report -> {args.output}"); return 0
if __name__ == "__main__": raise SystemExit(main())





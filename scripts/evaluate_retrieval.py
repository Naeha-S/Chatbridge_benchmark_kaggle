#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from continuitybench.metrics import context_size_tokens, irrelevant_inclusion_rate, retrieval_recall_at_k, timed_retrieval
from continuitybench.retrieval import BM25Retriever, DenseRetriever, HybridRetriever, KeywordRetriever, NoRetrievalBaseline
from continuitybench.schema import build_model_input


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate ContinuityBench retrieval baselines")
    parser.add_argument("--dataset", required=True, help="JSONL dataset path")
    parser.add_argument("--output", required=True, help="Output metrics JSON path")
    parser.add_argument("--k", type=int, default=5)
    return parser.parse_args()


def load_cases(path: Path) -> list[dict]:
    cases = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def evaluate_retriever(name: str, factory, cases: list[dict], k: int) -> dict:
    recalls = []
    latencies = []
    ctx_sizes = []
    distractor_rates = []

    for case in cases:
        model_input = build_model_input(case)
        docs = [turn["content"] for turn in model_input["source_conversation"]]
        retriever = factory(docs)
        query = model_input["handoff_task"]

        ranked, latency_ms = timed_retrieval(retriever, query, k)
        retrieved_docs = [doc for _, doc, _ in ranked]

        recalls.append(retrieval_recall_at_k(case["required_facts"], retrieved_docs))
        latencies.append(latency_ms)
        ctx_sizes.append(context_size_tokens(retrieved_docs))
        distractor_rates.append(irrelevant_inclusion_rate(retrieved_docs, case["irrelevant_distractor_facts"]))

    return {
        "name": name,
        "recall_at_k": mean(recalls) if recalls else 0.0,
        "latency_ms": mean(latencies) if latencies else 0.0,
        "context_size_tokens": mean(ctx_sizes) if ctx_sizes else 0.0,
        "irrelevant_context_inclusion": mean(distractor_rates) if distractor_rates else 0.0,
    }


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.dataset)
    cases = load_cases(dataset_path)

    baselines = [
        ("no_retrieval", NoRetrievalBaseline),
        ("keyword", KeywordRetriever),
        ("bm25", BM25Retriever),
        ("dense", DenseRetriever),
        ("hybrid", HybridRetriever),
    ]

    output = {
        "dataset": str(dataset_path),
        "k": args.k,
        "num_cases": len(cases),
        "metrics": [evaluate_retriever(name, factory, cases, args.k) for name, factory in baselines],
        "note": "Retrieval metrics are reported separately from end-to-end answer quality.",
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Evaluation report -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

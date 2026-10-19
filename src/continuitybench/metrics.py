from __future__ import annotations

import time
from typing import Any


def retrieval_recall_at_k(required_facts: list[str], retrieved_docs: list[str]) -> float:
    if not required_facts:
        return 1.0
    hits = 0
    joined = " ".join(retrieved_docs).lower()
    for fact in required_facts:
        if fact.lower() in joined:
            hits += 1
    return hits / len(required_facts)


def fact_preservation(predicted_state: dict[str, Any], expected_state: dict[str, Any]) -> float:
    expected = set(expected_state.get("active_facts", []))
    predicted = set(predicted_state.get("active_facts", []))
    if not expected:
        return 1.0
    return len(expected & predicted) / len(expected)


def stale_fact_error_rate(predicted_state: dict[str, Any], expected_state: dict[str, Any]) -> float:
    stale = set(expected_state.get("superseded", []))
    predicted = set(predicted_state.get("active_facts", []))
    if not stale:
        return 0.0
    return len(stale & predicted) / len(stale)


def contradiction_rate(predicted_state: dict[str, Any], required_constraints: list[str]) -> float:
    contradictions = set(predicted_state.get("contradicted_constraints", []))
    if not required_constraints:
        return 0.0
    return len(contradictions) / len(required_constraints)


def irrelevant_inclusion_rate(retrieved_docs: list[str], distractors: list[str]) -> float:
    if not distractors:
        return 0.0
    joined = " ".join(retrieved_docs).lower()
    hits = sum(1 for d in distractors if d.lower() in joined)
    return hits / len(distractors)


def context_size_tokens(retrieved_docs: list[str]) -> int:
    return len(" ".join(retrieved_docs).split())


def timed_retrieval(retriever, query: str, k: int) -> tuple[list[tuple[int, str, float]], float]:
    start = time.perf_counter()
    results = retriever.retrieve(query, k=k)
    latency_ms = (time.perf_counter() - start) * 1000.0
    return results, latency_ms

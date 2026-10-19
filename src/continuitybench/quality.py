from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from typing import Any

from .schema import validate_case


def detect_duplicates(cases: list[dict[str, Any]]) -> list[tuple[str, str]]:
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str]] = []
    for case in cases:
        key = json.dumps(
            {
                "conversation": case["source_conversation"],
                "handoff_task": case["handoff_task"],
                "required_facts": sorted(case["required_facts"]),
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        if digest in seen:
            duplicates.append((seen[digest], case["case_id"]))
        else:
            seen[digest] = case["case_id"]
    return duplicates


def referential_consistency_errors(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    joined = " ".join(turn["content"] for turn in case["source_conversation"])
    for update in case["superseded_facts"]:
        if update["old"] not in joined:
            errors.append(f"missing old superseded fact in conversation: {update['old']}")
        if update["new"] not in joined:
            errors.append(f"missing new superseding fact in conversation: {update['new']}")
        if update["new"] not in case["expected_continuity_state"].get("active_facts", []):
            errors.append(f"new superseding fact not active: {update['new']}")
    return errors


def semantic_validation_errors(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    active_facts = set(case["expected_continuity_state"].get("active_facts", []))
    for fact in case["required_facts"]:
        if fact not in active_facts:
            errors.append(f"required fact missing from expected active facts: {fact}")

    stale = set(case["expected_continuity_state"].get("superseded", []))
    for update in case["superseded_facts"]:
        if update["old"] not in stale:
            errors.append(f"superseded old fact missing from superseded list: {update['old']}")
    return errors


def validate_dataset(cases: list[dict[str, Any]]) -> dict[str, Any]:
    schema_errors: dict[str, list[str]] = {}
    reference_errors: dict[str, list[str]] = {}
    semantic_errors: dict[str, list[str]] = {}

    for case in cases:
        s_errors = validate_case(case)
        if s_errors:
            schema_errors[case.get("case_id", "unknown")] = s_errors

        r_errors = referential_consistency_errors(case)
        if r_errors:
            reference_errors[case["case_id"]] = r_errors

        sem_errors = semantic_validation_errors(case)
        if sem_errors:
            semantic_errors[case["case_id"]] = sem_errors

    return {
        "total_cases": len(cases),
        "schema_errors": schema_errors,
        "referential_errors": reference_errors,
        "semantic_errors": semantic_errors,
        "duplicate_pairs": detect_duplicates(cases),
    }


def split_dataset(cases: list[dict[str, Any]], seed: int = 7, ratios: tuple[float, float, float] = (0.7, 0.15, 0.15)) -> dict[str, list[dict[str, Any]]]:
    if abs(sum(ratios) - 1.0) > 1e-9:
        raise ValueError("ratios must sum to 1.0")
    shuffled = list(cases)
    random.Random(seed).shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * ratios[0])
    n_dev = int(n * ratios[1])
    return {
        "train": shuffled[:n_train],
        "dev": shuffled[n_train : n_train + n_dev],
        "test": shuffled[n_train + n_dev :],
    }


def coverage_report(cases: list[dict[str, Any]]) -> dict[str, Any]:
    categories = Counter(cat for case in cases for cat in case["failure_categories"])
    difficulties = Counter(case["difficulty_level"] for case in cases)
    return {
        "count": len(cases),
        "failure_category_counts": dict(categories),
        "difficulty_counts": dict(difficulties),
    }

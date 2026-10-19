from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

REVIEW_STATUSES = {"unreviewed", "accepted", "corrected", "rejected"}
ISSUE_CATEGORIES = {"none", "temporal_update", "stale_fact", "ambiguous_expected_state", "invalid_distractor", "answer_leakage", "other"}


def build_review_record(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "scenario_family_id": case.get("scenario_family_id"),
        "source_conversation": case["source_conversation"],
        "handoff_task": case["handoff_task"],
        "gold_state": case["expected_continuity_state"],
        "required_facts": case["required_facts"],
        "required_constraints": case["required_constraints"],
        "superseded_facts": case["superseded_facts"],
        "irrelevant_distractor_facts": case["irrelevant_distractor_facts"],
        "checks": {
            "temporal_updates_correct": None,
            "stale_facts_correctly_marked": None,
            "expected_state_unambiguous": None,
            "distractors_valid": None,
            "no_answer_leakage": None,
        },
        "review": {"status": "unreviewed", "reviewer_decision": None, "issue_category": "none", "correction_notes": ""},
    }


def export_review_file(cases: list[dict[str, Any]], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(build_review_record(case), ensure_ascii=False) + "\n")
    return path


def review_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(record.get("review", {}).get("status", "unreviewed") for record in records)
    issues = Counter(record.get("review", {}).get("issue_category", "none") for record in records)
    invalid_statuses = sorted(set(statuses) - REVIEW_STATUSES)
    invalid_issues = sorted(set(issues) - ISSUE_CATEGORIES)
    return {"total_cases": len(records), "status_counts": dict(statuses), "issue_category_counts": dict(issues), "invalid_statuses": invalid_statuses, "invalid_issue_categories": invalid_issues, "semantically_validated": statuses.get("unreviewed", 0) == 0 and not invalid_statuses}


def summarize_review_file(path: str | Path, output: str | Path) -> Path:
    records = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(review_summary(records), indent=2), encoding="utf-8")
    return destination

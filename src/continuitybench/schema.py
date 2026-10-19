from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "1.0"

REQUIRED_FIELDS = {
    "schema_version",
    "case_id",
    "source_conversation",
    "handoff_task",
    "required_facts",
    "required_constraints",
    "superseded_facts",
    "irrelevant_distractor_facts",
    "expected_continuity_state",
    "failure_categories",
    "difficulty_level",
    "evaluation_criteria",
    "scenario_types",
}


def validate_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_FIELDS.difference(case)
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")

    if case.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version: {case.get('schema_version')}")

    if not case.get("case_id"):
        errors.append("case_id must be non-empty")

    if not isinstance(case.get("source_conversation"), list) or not case.get("source_conversation"):
        errors.append("source_conversation must be a non-empty list")

    for key in (
        "required_facts",
        "required_constraints",
        "superseded_facts",
        "irrelevant_distractor_facts",
        "failure_categories",
        "scenario_types",
    ):
        if not isinstance(case.get(key), list):
            errors.append(f"{key} must be a list")

    if case.get("difficulty_level") not in {"easy", "medium", "hard"}:
        errors.append("difficulty_level must be one of easy/medium/hard")

    if not isinstance(case.get("evaluation_criteria"), dict) or not case.get("evaluation_criteria"):
        errors.append("evaluation_criteria must be a non-empty dict")

    if not isinstance(case.get("expected_continuity_state"), dict):
        errors.append("expected_continuity_state must be a dict")

    return errors


def build_model_input(case: dict[str, Any]) -> dict[str, Any]:
    """Return model-facing data without answer/leakage fields."""
    return {
        "case_id": case["case_id"],
        "source_conversation": case["source_conversation"],
        "handoff_task": case["handoff_task"],
    }

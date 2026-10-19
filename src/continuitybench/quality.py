from __future__ import annotations
import hashlib, json
from collections import Counter, defaultdict
from typing import Any
from .schema import validate_case

def detect_duplicates(cases: list[dict[str, Any]]) -> list[tuple[str, str]]:
    seen, duplicates = {}, []
    for case in cases:
        key = json.dumps({"conversation": case["source_conversation"], "handoff_task": case["handoff_task"], "required_facts": sorted(case["required_facts"])}, sort_keys=True)
        digest = hashlib.sha256(key.encode()).hexdigest()
        if digest in seen: duplicates.append((seen[digest], case["case_id"]))
        else: seen[digest] = case["case_id"]
    return duplicates

def referential_consistency_errors(case: dict[str, Any]) -> list[str]:
    text = " ".join(turn["content"] for turn in case["source_conversation"])
    errors = []
    for update in case["superseded_facts"]:
        if update["old"] not in text: errors.append(f"missing old superseded fact: {update['old']}")
        if update["new"] not in text: errors.append(f"missing new superseding fact: {update['new']}")
        if update["new"] not in case["expected_continuity_state"].get("active_constraints", []) and update["new"] not in case["expected_continuity_state"].get("active_facts", []): errors.append(f"new superseding fact not active: {update['new']}")
    return errors

def _provenance_errors(case: dict[str, Any]) -> list[str]:
    errors = []
    provenance = case["expected_continuity_state"].get("provenance", {})
    state = case["expected_continuity_state"]
    for key in ("active_facts", "active_constraints", "unresolved_tasks", "superseded"):
        items = state.get(key, [])
        records = provenance.get(key, [])
        if len(items) != len(records): errors.append(f"provenance count mismatch for {key}")
        for record in records:
            if not record.get("item") or record.get("evidence_type") not in {"source_grounded", "permitted_inference"} or not record.get("source_turns"): errors.append(f"invalid provenance for {key}")
    return errors

def _contradiction_is_real(case: dict[str, Any]) -> bool:
    old = case["evaluation_criteria"].get("conflicts_with", "").lower()
    new = case["evaluation_criteria"].get("requires_resolution", "").lower()
    pairs = [("publish", "hold publication"), ("full mailing list", "only with the review group"), ("production data", "synthetic data")]
    return any(left in old and right in new for left, right in pairs)
def semantic_validation_errors(case: dict[str, Any]) -> list[str]:
    errors, text = _provenance_errors(case), " ".join(turn["content"] for turn in case["source_conversation"])
    state, active = case["expected_continuity_state"], set(case["expected_continuity_state"].get("active_facts", []))
    for fact in case["required_facts"]:
        if fact not in active: errors.append(f"required fact missing from active facts: {fact}")
    if set(state.get("superseded", [])) != {x["old"] for x in case["superseded_facts"]}: errors.append("superseded state does not match superseded facts")
    for category in case["scenario_types"]:
        if category == "temporal_changes" and (not case["superseded_facts"] or not any("moved" in x["new"].lower() or "changed" in x["new"].lower() for x in case["superseded_facts"])): errors.append("temporal case lacks distinguishable update")
        elif category == "superseded_decisions" and (not case["superseded_facts"] or not any(x["old"] in text and x["new"] in text for x in case["superseded_facts"])): errors.append("superseded decision lacks old/new evidence")
        elif category == "contradictory_instructions" and (not case["required_constraints"] or not case["evaluation_criteria"].get("conflicts_with") or not _contradiction_is_real(case)): errors.append("contradiction case lacks semantic conflict")
        elif category == "unfinished_tasks" and (not state.get("unresolved_tasks") or not any(word in text.lower() for word in ("pending", "blocked", "awaiting"))): errors.append("unfinished case lacks unresolved task status")
        elif category == "forgotten_facts" and (not case["required_facts"] or not case["handoff_task"]): errors.append("forgotten-fact case lacks relevant handoff fact")
        elif category == "irrelevant_context" and (not case["irrelevant_distractor_facts"] or not all(d in text for d in case["irrelevant_distractor_facts"])): errors.append("irrelevant-context case lacks grounded distractor")
    return errors

def validate_dataset(cases: list[dict[str, Any]]) -> dict[str, Any]:
    schema_errors, reference_errors, semantic_errors = {}, {}, {}
    for case in cases:
        if (e := validate_case(case)): schema_errors[case.get("case_id", "unknown")] = e
        if (e := referential_consistency_errors(case)): reference_errors[case["case_id"]] = e
        if (e := semantic_validation_errors(case)): semantic_errors[case["case_id"]] = e
    return {"total_cases": len(cases), "schema_errors": schema_errors, "referential_errors": reference_errors, "semantic_errors": semantic_errors, "duplicate_pairs": detect_duplicates(cases)}

def _family_id(case: dict[str, Any]) -> str:
    return case.get("scenario_family_id") or "|".join(sorted(case.get("scenario_types", [])))

def split_dataset(cases: list[dict[str, Any]], seed: int = 7, ratios: tuple[float, float, float] = (0.7, 0.15, 0.15)) -> dict[str, list[dict[str, Any]]]:
    if abs(sum(ratios) - 1.0) > 1e-9 or any(r < 0 for r in ratios): raise ValueError("ratios must be non-negative and sum to 1.0")
    groups = defaultdict(list)
    for case in cases: groups[_family_id(case)].append(case)
    ordered = sorted(groups.items(), key=lambda item: hashlib.sha256(f"{seed}:{item[0]}".encode()).hexdigest())
    targets = [len(cases) * ratio for ratio in ratios]; names = ["train", "dev", "test"]; splits = {name: [] for name in names}
    for _, members in ordered:
        available = [i for i, name in enumerate(names) if len(splits[name]) < targets[i]]
        index = min(available or range(3), key=lambda i: (len(splits[names[i]]) / ratios[i] if ratios[i] else float("inf"), i))
        splits[names[index]].extend(members)
    return splits

def coverage_report(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {"count": len(cases), "failure_category_counts": dict(Counter(x for c in cases for x in c["failure_categories"])), "difficulty_counts": dict(Counter(c["difficulty_level"] for c in cases)), "scenario_family_counts": dict(Counter(_family_id(c) for c in cases))}


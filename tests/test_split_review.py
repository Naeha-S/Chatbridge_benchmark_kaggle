import json
from pathlib import Path

from continuitybench.generator import generate_cases
from continuitybench.quality import split_dataset
from continuitybench.review import export_review_file, review_summary
from continuitybench.schema import build_model_input


def test_group_split_is_deterministic_and_has_no_family_leakage():
    cases = generate_cases(84, seed=7)
    first = split_dataset(cases, seed=7)
    second = split_dataset(cases, seed=7)
    assert first == second
    memberships = {}
    for split, members in first.items():
        for case in members:
            family = case["scenario_family_id"]
            assert family not in memberships or memberships[family] == split
            memberships[family] = split
    assert sum(map(len, first.values())) == len(cases)


def test_small_group_split_does_not_split_group():
    cases = generate_cases(2, seed=7)
    splits = split_dataset(cases, seed=7)
    assert all(len(items) == 0 or {case["scenario_family_id"] for case in items} for items in splits.values())


def test_review_export_is_evaluator_only_and_summary_counts():
    cases = generate_cases(3, seed=7)
    output = Path("reports/generated/_test_review.jsonl")
    export_review_file(cases, output)
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(records) == 3
    assert all(record["review"]["status"] == "unreviewed" for record in records)
    assert "expected_continuity_state" not in build_model_input(cases[0])
    assert review_summary(records)["status_counts"] == {"unreviewed": 3}
    output.unlink()



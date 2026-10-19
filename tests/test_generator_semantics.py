from continuitybench.generator import generate_cases
from continuitybench.quality import split_dataset, validate_dataset
from continuitybench.schema import build_model_input

def test_generated_cases_have_semantically_valid_categories():
    report = validate_dataset(generate_cases(84, seed=7))
    assert report["schema_errors"] == {}
    assert report["referential_errors"] == {}
    assert report["semantic_errors"] == {}
    assert report["duplicate_pairs"] == []

def test_families_are_template_ids_not_category_only():
    cases = generate_cases(84, seed=7)
    assert any(case["scenario_family_id"] != "|".join(sorted(case["scenario_types"])) for case in cases)

def test_group_split_has_no_family_leakage_and_is_deterministic():
    cases = generate_cases(84, seed=7)
    first, second = split_dataset(cases, 7), split_dataset(cases, 7)
    assert first == second
    seen = {}
    for name, group in first.items():
        for case in group:
            assert seen.setdefault(case["scenario_family_id"], name) == name

def test_model_input_does_not_include_gold_state():
    case = generate_cases(1)[0]
    model_input = build_model_input(case)
    assert "expected_continuity_state" not in model_input
    assert "evaluation_criteria" not in model_input

def test_distractors_do_not_reveal_irrelevance():
    for case in generate_cases(84, seed=7):
        text = " ".join(turn["content"] for turn in case["source_conversation"]).lower()
        assert "unrelated to the handoff" not in text


def test_gold_state_has_provenance_for_every_item():
    for case in generate_cases(84, seed=7):
        state = case["expected_continuity_state"]
        provenance = state["provenance"]
        for key in ("active_facts", "active_constraints", "unresolved_tasks", "superseded"):
            assert len(state.get(key, [])) == len(provenance[key])
            assert all(item["source_turns"] for item in provenance[key])


def test_contradiction_cases_are_semantically_incompatible():
    for case in generate_cases(84, seed=7):
        if "contradictory_instructions" in case["scenario_types"]:
            assert case["evaluation_criteria"]["conflicts_with"] != case["evaluation_criteria"]["requires_resolution"]

def test_deadline_change_alone_does_not_create_unresolved_task():
    for case in generate_cases(84, seed=7):
        if case["scenario_types"] == ["temporal_changes"]:
            assert not any("readiness" in task.lower() or "confirm" in task.lower() for task in case["expected_continuity_state"]["unresolved_tasks"])


def test_approval_change_alone_does_not_create_request_task():
    for case in generate_cases(84, seed=7):
        if case["scenario_types"] == ["superseded_decisions"]:
            assert not any("request" in task.lower() for task in case["expected_continuity_state"]["unresolved_tasks"])


def test_provenance_has_exact_item_turn_ids_and_explanations():
    for case in generate_cases(84, seed=7):
        for key, records in case["expected_continuity_state"]["provenance"].items():
            for record in records:
                assert record["item"]
                assert record["source_turn_ids"]
                assert record["explanation"]
                assert record["evidence_type"] in {"source_grounded", "permitted_inference"}


def test_deadline_only_task_does_not_request_next_action():
    for case in generate_cases(84, seed=7):
        if case["scenario_types"] == ["temporal_changes"]:
            task = case["handoff_task"].lower()
            assert "next action" not in task
            assert "current deadline" in task
            assert "superseded" in task

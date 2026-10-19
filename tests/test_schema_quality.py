from continuitybench.generator import generate_cases
from continuitybench.quality import split_dataset, validate_dataset
from continuitybench.schema import build_model_input, validate_case


def test_schema_validation_accepts_generated_case():
    case = generate_cases(1, seed=7)[0]
    assert validate_case(case) == []


def test_model_input_omits_expected_state_to_reduce_leakage():
    case = generate_cases(1, seed=7)[0]
    model_input = build_model_input(case)
    assert "expected_continuity_state" not in model_input
    assert set(model_input.keys()) == {"case_id", "source_conversation", "handoff_task"}


def test_split_has_no_overlap():
    cases = generate_cases(30, seed=7)
    splits = split_dataset(cases, seed=7)
    ids = {name: {case["case_id"] for case in group} for name, group in splits.items()}
    assert ids["train"].isdisjoint(ids["dev"])
    assert ids["train"].isdisjoint(ids["test"])
    assert ids["dev"].isdisjoint(ids["test"])


def test_validation_reports_clean_generated_cases():
    cases = generate_cases(15, seed=13)
    report = validate_dataset(cases)
    assert report["schema_errors"] == {}
    assert report["referential_errors"] == {}
    assert report["semantic_errors"] == {}
    assert report["duplicate_pairs"] == []

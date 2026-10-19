from continuitybench.generator import generate_cases
from continuitybench.schema import build_model_input

def test_model_input_excludes_evaluator_only_fields_and_values():
    case = generate_cases(1, seed=7)[0]
    model_input = build_model_input(case)
    serialized = repr(model_input)
    for key in ("expected_continuity_state", "evaluation_criteria", "required_facts", "superseded_facts"):
        assert key not in model_input
    assert repr(case["expected_continuity_state"]) not in serialized
    assert repr(case["evaluation_criteria"]) not in serialized

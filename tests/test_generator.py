from continuitybench.generator import generate_cases


def test_generator_is_deterministic_for_seed():
    first = generate_cases(10, seed=11)
    second = generate_cases(10, seed=11)
    assert first == second


def test_generator_covers_multi_failure_scenarios():
    cases = generate_cases(14, seed=7)
    assert any("multi_failure" in case["failure_categories"] for case in cases)

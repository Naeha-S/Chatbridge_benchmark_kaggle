from continuitybench.metrics import contradiction_rate, fact_preservation, irrelevant_inclusion_rate, retrieval_recall_at_k, stale_fact_error_rate

def test_metric_edge_cases_and_denominators():
    assert retrieval_recall_at_k([], []) == 1.0
    assert retrieval_recall_at_k(["a", "a", "b"], ["a"]) == 0.5
    assert fact_preservation({}, {}) == 1.0
    assert fact_preservation({"active_facts": ["a"]}, {"active_facts": ["a", "b"]}) == 0.5
    assert stale_fact_error_rate({"active_facts": ["old"]}, {"superseded": ["old", "older"]}) == 0.5
    assert stale_fact_error_rate({}, {}) == 0.0
    assert contradiction_rate({"contradicted_constraints": ["c1"]}, ["c1", "c2"]) == 0.5
    assert contradiction_rate({}, []) == 0.0
    assert irrelevant_inclusion_rate(["d"], ["d", "e"]) == 0.5
    assert irrelevant_inclusion_rate([], []) == 0.0

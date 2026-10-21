# ContinuityBench Cross-Model Handoff Analysis

Input: `reports\generated\current\cross_model_handoff_ollama_llama31_qwen3_source_retrieval_audit_20261020_full.json`

Valid completed cases: **84/84**. This is a descriptive analysis of one local run; no significance tests were performed.

## Aggregate Metrics

| Condition | Metric | N | Mean | Median | SD | Min | Max | Zero % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| transfer | fact_preservation | 84 | 0.1349 | 0.0000 | 0.2124 | 0.0000 | 0.5000 | 70.2381 |
| transfer | stale_fact_error_rate | 84 | 0.1667 | 0.0000 | 0.3727 | 0.0000 | 1.0000 | 83.3333 |
| transfer | contradiction_rate | 84 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 100.0000 |
| transfer | answer_required_fact_coverage | 84 | 0.0298 | 0.0000 | 0.1183 | 0.0000 | 0.5000 | 94.0476 |
| no_transfer | fact_preservation | 84 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 100.0000 |
| no_transfer | stale_fact_error_rate | 84 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 100.0000 |
| no_transfer | contradiction_rate | 84 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 100.0000 |
| no_transfer | answer_required_fact_coverage | 84 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 100.0000 |
| source_retrieval | fact_preservation | 84 | 0.0179 | 0.0000 | 0.0928 | 0.0000 | 0.5000 | 96.4286 |
| source_retrieval | stale_fact_error_rate | 84 | 0.0238 | 0.0000 | 0.1525 | 0.0000 | 1.0000 | 97.6190 |
| source_retrieval | contradiction_rate | 84 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 100.0000 |
| source_retrieval | answer_required_fact_coverage | 84 | 0.0119 | 0.0000 | 0.0762 | 0.0000 | 0.5000 | 97.6190 |

## Paired Comparisons

| Comparison | Metric | Mean difference | Median difference | First favorable | Second favorable | Ties | Direction |
|---|---|---:|---:|---:|---:|---:|---|
| transfer_vs_no_transfer | fact_preservation | 0.1349 | 0.0000 | 25 | 0 | 59 | higher_better |
| transfer_vs_no_transfer | stale_fact_error_rate | 0.1667 | 0.0000 | 0 | 14 | 70 | lower_better |
| transfer_vs_no_transfer | contradiction_rate | 0.0000 | 0.0000 | 0 | 0 | 84 | lower_better |
| transfer_vs_no_transfer | answer_required_fact_coverage | 0.0298 | 0.0000 | 5 | 0 | 79 | higher_better |
| source_retrieval_vs_no_transfer | fact_preservation | 0.0179 | 0.0000 | 3 | 0 | 81 | higher_better |
| source_retrieval_vs_no_transfer | stale_fact_error_rate | 0.0238 | 0.0000 | 0 | 2 | 82 | lower_better |
| source_retrieval_vs_no_transfer | contradiction_rate | 0.0000 | 0.0000 | 0 | 0 | 84 | lower_better |
| source_retrieval_vs_no_transfer | answer_required_fact_coverage | 0.0119 | 0.0000 | 2 | 0 | 82 | higher_better |
| transfer_vs_source_retrieval | fact_preservation | 0.1171 | 0.0000 | 23 | 1 | 60 | higher_better |
| transfer_vs_source_retrieval | stale_fact_error_rate | 0.1429 | 0.0000 | 0 | 12 | 72 | lower_better |
| transfer_vs_source_retrieval | contradiction_rate | 0.0000 | 0.0000 | 0 | 0 | 84 | lower_better |
| transfer_vs_source_retrieval | answer_required_fact_coverage | 0.0179 | 0.0000 | 4 | 1 | 79 | higher_better |

## Interpretation

- `fact_preservation` and `answer_required_fact_coverage` are higher-is-better exact-string measures.
- `stale_fact_error_rate` and `contradiction_rate` are lower-is-better error measures.
- BM25 evidence is lexical, not semantic. Exact-string scoring can mark valid paraphrases incorrect.
- Zero stale-fact or contradiction scores do not prove complete correctness.
- Models share one local Ollama environment; this is cross-model evaluation, not independent replication.
- Category and difficulty groups should be interpreted with their reported sample sizes; no inferential claims are made.

## Conclusion

The run is structurally complete: all 84 IDs have one completed record and retrieval evidence. This supports descriptive comparison only. It does not establish generalization, semantic correctness, or statistical superiority.

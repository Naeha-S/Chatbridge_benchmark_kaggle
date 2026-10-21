# ContinuityBench v1

ContinuityBench is a frozen 84-case dataset for conversational continuity and two-stage model handoff evaluation. This package is prepared as a Kaggle Dataset upload, not a competition entry.

## Contents

- `data/continuitybench_v1.jsonl`: original 84-case JSONL dataset. It includes gold evaluator fields; do not expose those fields to evaluated models.
- `data/schema.md`, `data/data_dictionary.md`: schema and field definitions.
- `results/per_case_results.csv`: per-case metrics from the completed local Llama-to-Qwen source-retrieval run.
- `analysis/`: aggregate, paired, category, and difficulty analyses.
- `metadata/provenance.json`: package metadata and SHA-256 hashes.
- `metadata/source_experiment_manifest.json`: diagnostic experiment manifest, kept separate from clean benchmark inputs.

## Experiment

The completed run used Ollama `llama3.1:8b` as Model A and `qwen3:4b` as Model B. Conditions were transfer artifact, no transfer, and lexical source retrieval. Source retrieval ranked the complete source conversation with deterministic BM25 using the handoff task as query and `k=5`; it is not semantic retrieval.

The analysis uses the existing metric definitions without modification: `fact_preservation`, `stale_fact_error_rate`, `contradiction_rate`, and `answer_required_fact_coverage`. The metrics are exact-string or structured-set measures and should not be read as semantic validity.

## Limitations

This is one local run, not evidence of generalization or statistical superiority. Both models ran in one local Ollama environment. Exact-string matching can penalize paraphrases. Zero contradiction or stale-fact error does not prove complete correctness. Human review and owner confirmation of licensing/redistribution permissions remain publication responsibilities.

## Notebook

Use `continuitybench_analysis.ipynb` with this package as the Kaggle input directory. It performs offline validation and descriptive analysis only; it does not call Ollama or any API.

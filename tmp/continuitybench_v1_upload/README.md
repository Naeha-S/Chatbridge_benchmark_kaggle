# ContinuityBench v1 Release Candidate

This directory contains only Kaggle-specific documentation and the offline analysis notebook. The canonical dataset, experiment results, analysis outputs, source code, and tests remain in their existing repository locations.

## What It Evaluates

ContinuityBench evaluates whether a target model can reconstruct and answer a conversational handoff using information from a source interaction. The frozen benchmark contains 84 cases covering forgotten facts, superseded decisions, contradictory instructions, temporal changes, unfinished tasks, irrelevant context, and combinations of these conditions.

## Experimental Conditions

The completed local experiment compares:

- **Transfer:** Model A produces a structured handoff artifact; Model B receives that artifact and the handoff task.
- **No-transfer:** Model B receives the handoff task without transferred context.
- **BM25 source retrieval:** Model B receives the handoff task plus up to five positive-scoring source turns selected by deterministic lexical BM25 retrieval.

The retrieval condition is lexical, not semantic.

## Dataset and Files

The packager assembles the temporary upload from canonical sources:

- `data/continuitybench_v1.jsonl`: 84 cases in the existing JSONL schema.
- `data/README.md`: available dataset documentation and field notes.
- `results/per_case_results.csv`: per-case metrics from the included run.
- `analysis/`: aggregate, paired, category, difficulty, validation, and analysis reports.
- `continuitybench_analysis.ipynb`: offline analysis notebook.
- `LICENSE_STATUS.md`: unresolved licensing status; not a license grant.

The dataset includes evaluator-only gold fields. These fields must not be included in model-facing inputs.

## Included Experiment

The included run used local Ollama models:

- Model A: `llama3.1:8b`
- Model B: `qwen3:4b`
- Backend: local Ollama

The existing metric definitions are preserved: `fact_preservation`, `stale_fact_error_rate`, `contradiction_rate`, and `answer_required_fact_coverage`. Exact-string and set-based scoring can mark valid paraphrases as incorrect. Error metrics of zero do not prove complete correctness.

## Offline Notebook

The notebook loads files from a configurable `CONTINUITYBENCH_INPUT_DIR`, defaulting to `/kaggle/input/continuitybench-v1` when available and the current directory otherwise. It uses local tabular/plotting libraries only. It does not call Ollama, require API credentials, download models, or perform inference.

## Limitations and Release Status

The reported results are from one local run. They do not establish generalization, statistical superiority, or independent replication. The owner confirms that the 84 conversations were generated specifically for this project using ChatGPT/Codex, manually reviewed, and, to the owner's knowledge, did not use third-party conversations or copied external material. This is owner-provided provenance, not independent verification. Synthetic provenance and non-confidentiality of names, references, identifiers, and conversations are not independently verified.

Public distribution still requires explicit license and redistribution decisions for the dataset, gold labels, human-review artifacts, generated model outputs, and derived files. Local documentation did not establish complete Llama 3.1 or Qwen3 output terms; those terms must be checked before upload. The root repository MIT license is not assumed to cover all of those artifacts. See `LICENSE_STATUS.md`; the release candidate is not cleared for public distribution until these decisions are resolved.

## Build a Temporary Upload

```powershell
py scripts/package_kaggle.py --output .tmp/kaggle_upload_20261021
```

The packager refuses to overwrite an existing output directory, excludes the diagnostic source experiment manifest, validates 84 unique dataset IDs and matching result rows, and writes a manifest that records the unresolved license blocker.


# ContinuityBench (Phase 1 scaffold)

ContinuityBench is a reproducible benchmark scaffold for evaluating conversational continuity across session/model handoffs.

> **Status:** Proposed benchmark. Novelty claims are deferred until related work review is completed.

## Phase 1 deliverables in this repository

- `src/continuitybench/` core schema, generation, validation, retrieval baselines, and metrics.
- `data/` generated synthetic examples (created by scripts; ignored by default under `data/generated/`).
- `tests/` focused unit tests.
- `notebooks/` exploratory analysis workspace.
- `scripts/` command-line dataset generation and baseline evaluation scripts.
- `reports/` machine-readable metrics and QA summaries (generated into `reports/generated/current/`).

## Architecture (initial)

- `schema.py`: versioned case schema and strict validation.
- `generator.py`: deterministic synthetic case generation with scenario composition.
- `quality.py`: duplicate detection, referential consistency, semantic checks, split assignment, and coverage reporting.
- `retrieval.py`: independently testable retrieval baselines: keyword, BM25, dense (offline hash fallback / optional sentence-transformers), hybrid, and no-retrieval.
- `metrics.py`: metric definitions and deterministic evaluation utilities.

## Dataset schema (v1.0)

Each case includes:

- `schema_version`
- `case_id`
- `source_conversation`
- `handoff_task`
- `required_facts`
- `required_constraints`
- `superseded_facts`
- `irrelevant_distractor_facts`
- `expected_continuity_state`
- `failure_categories`
- `difficulty_level`
- `evaluation_criteria`
- `scenario_types`

### Leakage control

The benchmark uses `build_model_input(case)` to create model-facing input that excludes `expected_continuity_state` and evaluator-only annotations. Evaluations must only feed model-facing inputs to tested systems.

## Evaluation protocol (Phase 1)

Retrieval and continuity metrics are measured separately from end-to-end generation quality.

Definitions:

- **Retrieval Recall@k**: fraction of required facts that appear in top-k retrieved context chunks.
- **Fact preservation**: fraction of expected active facts preserved by predicted state.
- **Stale-fact error rate**: fraction of superseded facts incorrectly retained as active.
- **Contradiction rate**: fraction of required constraints contradicted in predicted state.
- **Irrelevant-context inclusion**: fraction of distractors included in selected context.
- **Latency (ms)**: measured wall-time per retrieval call.
- **Context size (tokens)**: whitespace-token count of selected context.

## Quality assurance

Implemented checks:

- Schema validation
- Duplicate detection
- Referential consistency checks
- Deterministic train/dev/test split generation
- Deterministic random seeds
- Unit tests
- Coverage and dataset statistics report
- Semantic validation hooks

Schema validity alone is **not** treated as semantic validity. Sample review is required before release claims.

## Potential benchmark flaws & leakage risks to monitor

- Evaluator annotations accidentally passed into model inputs.
- Template artifacts enabling shortcut learning.
- Overlap leakage across train/dev/test via near-duplicate conversations.
- Mislabeling superseded facts in temporal-update scenarios.
- Conflating retrieval quality with final answer quality.

## Related work to investigate before novelty claims

- Benchmarks for long-context QA and memory retention.
- Work on conversational state tracking and dialogue memory.
- Studies on cross-session handoff reliability.
- Retrieval-augmented dialogue evaluation methods.
- Contradiction and stale-context detection in LLM systems.

## Milestones

1. **Phase 1 (current):** scaffold + synthetic data generator + QA + baseline retrieval metrics.
2. **Phase 2:** richer scenarios, human review protocol, and baseline expansion.
3. **Phase 3:** broader model evaluation + ablations + release candidate packaging.

## Reproducibility commands

```bash
python scripts/generate_dataset.py --output data/generated/continuitybench_v1.jsonl --count 84 --seed 7
python scripts/evaluate_retrieval.py --dataset data/generated/continuitybench_v1.jsonl --output reports/generated/current/retrieval_metrics.json --k 5
pytest
```

Each script writes machine-readable JSON including seeds/configuration and reports limitations/failures where applicable.

## Release setup and review workflow

Create a clean environment and install the project with its test dependencies:

```bash
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
```

The documented commands work after installation without setting `PYTHONPATH`:

```bash
.venv\Scripts\python scripts/generate_dataset.py --output data/generated/continuitybench_v1.jsonl --count 84 --seed 7
.venv\Scripts\python scripts/evaluate_retrieval.py --dataset data/generated/continuitybench_v1.jsonl --output reports/generated/current/retrieval_metrics.json --k 5
.venv\Scripts\python scripts/export_review.py --dataset data/generated/continuitybench_v1.jsonl --output reports/generated/review/review.jsonl --summary-output reports/generated/review/review_summary.json
```

Cases are split by the stable `scenario_family_id`; a family is never divided between train, dev, and test. Assignment is deterministic for a seed. If fewer than three families exist, one or more requested splits may be empty rather than leaking a family. Dense retrieval is offline by default and uses a deterministic hash fallback; install `.[dense]` only when the optional sentence-transformers model is available locally.

Review JSONL files are evaluator-only and must never be passed to a model. New records start as `unreviewed`; reviewers may set `accepted`, `corrected`, or `rejected`, with an issue category and correction notes. Only a zero-unreviewed summary is considered semantically reviewed, and even accepted cases require retained review evidence.

## Human review artifacts

Create a readable packet and editable workbook for the generated dataset:

```bash
py scripts/create_human_review_artifacts.py --dataset data/generated/continuitybench_v1.jsonl --markdown reports/generated/review/human_review_packet.md --xlsx reports/generated/review/human_review_workbook.xlsx
```

The workbook's `Case Review` sheet contains one row per case, source conversation, handoff task, gold state, provenance, editable checks, status, issue category, and correction notes. The `Summary` sheet counts review statuses. All generated cases start as `unreviewed`; automated checks must not be treated as human decisions.


## Local Ollama cross-model handoff

The primary runner supports an isolated local Ollama backend for the two-stage condition:

- Source artifact model: `llama3.1:8b`
- Target response model: `qwen3:4b`
- Endpoint: `http://localhost:11434`
- Output: `reports/generated/current/cross_model_handoff_ollama_llama31_qwen3.json`

Configure with environment variables or `.env` (never commit real credentials; Ollama is local):

```text
CB_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_SOURCE_MODEL=llama3.1:8b
OLLAMA_TARGET_MODEL=qwen3:4b
CB_RETRIES=2
```

Verify Ollama and models in PowerShell:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
(Invoke-RestMethod http://localhost:11434/api/tags).models.name
```

Run the first smoke test only after verification:

```powershell
py scripts/cross_model_handoff.py --backend ollama --case-id CB-00000 --retries 2
```

After inspecting the smoke-test output, run all 84 cases:

```powershell
py scripts/cross_model_handoff.py --backend ollama --retries 2
```

The runner persists after each case and resumes by skipping case IDs already present in the Ollama output. Use `--limit N` for a small batch. A valid score requires a completed comparison; connection, model-not-found, HTTP, empty-response, and JSON failures are recorded separately and are not scores. The existing Gemini/Hugging Face output is not reused or mixed with the Ollama output.

### Source-retrieval Ollama condition

For the corrected future experiment, use `--backend ollama_retrieval`. It ranks the complete source conversation with the existing deterministic BM25 implementation using the handoff task as the query. It selects up to five turns with score greater than zero, preserves `turn-{index}` provenance when source records lack explicit IDs, and formats selected turns in ranked order. Ties are stable by original turn index. Empty/no-match retrieval produces an explicit empty context. This is lexical BM25 retrieval, not semantic retrieval.

The corrected condition uses a separate output and does not overwrite the prior prefix-condition smoke result:

```powershell
py scripts/cross_model_handoff.py --backend ollama_retrieval --case-id CB-00000 --retries 2
py scripts/cross_model_handoff.py --backend ollama_retrieval --retries 2
```

Output: `reports/generated/current/cross_model_handoff_ollama_llama31_qwen3_source_retrieval.json`.

### Fresh auditable retrieval runs

To avoid resuming from either prior Ollama result, pass a new explicit `--output` path:

```powershell
py scripts/cross_model_handoff.py --backend ollama_retrieval --case-id CB-00000 --retries 2 --output reports/generated/current/cross_model_handoff_ollama_llama31_qwen3_source_retrieval_audit_20261020_smoke.json
py scripts/cross_model_handoff.py --backend ollama_retrieval --retries 2 --output reports/generated/current/cross_model_handoff_ollama_llama31_qwen3_source_retrieval_audit_20261020_full.json
```

Each auditable retrieval result stores `source_retrieval_evidence` separately from metrics, including selected turn metadata and the exact formatted target context.

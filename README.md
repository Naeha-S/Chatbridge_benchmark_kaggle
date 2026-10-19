# ContinuityBench (Phase 1 scaffold)

ContinuityBench is a reproducible benchmark scaffold for evaluating conversational continuity across session/model handoffs.

> **Status:** Proposed benchmark. Novelty claims are deferred until related work review is completed.

## Phase 1 deliverables in this repository

- `src/continuitybench/` core schema, generation, validation, retrieval baselines, and metrics.
- `data/` generated synthetic examples (created by scripts; ignored by default under `data/generated/`).
- `tests/` focused unit tests.
- `notebooks/` exploratory analysis workspace.
- `scripts/` command-line dataset generation and baseline evaluation scripts.
- `reports/` machine-readable metrics and QA summaries (generated into `reports/generated/`).

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
python scripts/evaluate_retrieval.py --dataset data/generated/continuitybench_v1.jsonl --output reports/generated/retrieval_metrics.json --k 5
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
.venv\Scripts\python scripts/evaluate_retrieval.py --dataset data/generated/continuitybench_v1.jsonl --output reports/generated/retrieval_metrics.json --k 5
.venv\Scripts\python scripts/export_review.py --dataset data/generated/continuitybench_v1.jsonl --output reports/generated/review.jsonl --summary-output reports/generated/review_summary.json
```

Cases are split by the stable `scenario_family_id`; a family is never divided between train, dev, and test. Assignment is deterministic for a seed. If fewer than three families exist, one or more requested splits may be empty rather than leaking a family. Dense retrieval is offline by default and uses a deterministic hash fallback; install `.[dense]` only when the optional sentence-transformers model is available locally.

Review JSONL files are evaluator-only and must never be passed to a model. New records start as `unreviewed`; reviewers may set `accepted`, `corrected`, or `rejected`, with an issue category and correction notes. Only a zero-unreviewed summary is considered semantically reviewed, and even accepted cases require retained review evidence.

## Human review artifacts

Create a readable packet and editable workbook for the generated dataset:

```bash
py scripts/create_human_review_artifacts.py --dataset data/generated/continuitybench_v1.jsonl --markdown reports/generated/human_review_packet.md --xlsx reports/generated/human_review_workbook.xlsx
```

The workbook's `Case Review` sheet contains one row per case, source conversation, handoff task, gold state, provenance, editable checks, status, issue category, and correction notes. The `Summary` sheet counts review statuses. All generated cases start as `unreviewed`; automated checks must not be treated as human decisions.

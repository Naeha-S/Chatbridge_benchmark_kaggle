# ContinuityBench Human Review Guide

## Scope and status

Review `reports/generated/review.jsonl` after generating the 84 cases with seed 7. This file intentionally contains evaluator-only gold information and must never be supplied to a model. New records are `unreviewed`; do not change status without reviewing the complete case. The current generated summary reports 84 unreviewed cases and zero semantically validated cases.

Run:

```text
py scripts/generate_dataset.py --output data/generated/continuitybench_v1.jsonl --count 84 --seed 7
py scripts/export_review.py --dataset data/generated/continuitybench_v1.jsonl --output reports/generated/review.jsonl --summary-output reports/generated/review_summary.json
```

## Decision procedure

For each case, inspect the source conversation, handoff task, gold state, required facts/constraints, superseded facts, and distractors. Set every check to `true` or `false`; use `null` only while unreviewed. Set `review.status` to exactly one of `accepted`, `corrected`, or `rejected` after reaching a decision. Set `review.reviewer_decision`, one `issue_category`, and concise `correction_notes`. A corrected case must record what was changed; a rejected case must explain why it cannot support a defensible gold state.

Accept only when all checks are true and the gold state is supported by the conversation. Correct when the intended state is recoverable but the annotation needs a specific edit. Reject when the state is ambiguous, unsupported, contradictory, or impossible to evaluate reliably.

## Objective acceptance criteria

- **Active facts:** Every listed active fact is explicitly supported by the conversation, is not superseded, and includes the latest value when updates exist. Every required fact is present unless the conversation clearly makes it unavailable.
- **Active constraints:** Each constraint is stated or unambiguously implied by the conversation, is actionable, and does not conflict with a later instruction. Constraints must not be invented from evaluator annotations.
- **Temporal updates and stale facts:** For each old/new pair, both statements occur in order; the new statement clearly updates the old one; the old value appears only in `superseded`, never as active; the latest state is represented in active facts.
- **Unresolved tasks:** Each unresolved task is grounded in an explicit unfinished request or commitment. Completed, hypothetical, or unsupported tasks must not be listed.
- **Distractors:** Each distractor is present in the source conversation, unrelated to the handoff objective, and should not alter the gold state. A distractor that changes a deadline, constraint, task, or required fact is not valid.
- **Ambiguous/unsupported state:** Mark `expected_state_unambiguous=false` if multiple plausible states remain, the conversation omits evidence, speaker/temporal order is unclear, or the gold state contains unsupported facts. This normally requires correction or rejection.
- **Evaluator leakage:** Mark `no_answer_leakage=true` only if the model-facing fields contain no gold state, evaluation criteria, required labels, review annotations, or hidden answer text. Review artifacts may contain these fields but are evaluator-only.

## Issue categories

Use `none` only for an accepted case. Use `temporal_update`, `stale_fact`, `ambiguous_expected_state`, `invalid_distractor`, `answer_leakage`, or `other` for a case needing correction/rejection. Automated schema, referential, and semantic checks are evidence for triage only; they are not human decisions and must not change review status automatically.

After review, rerun `export_review.py`'s summary step and preserve the JSONL plus summary as the review record.

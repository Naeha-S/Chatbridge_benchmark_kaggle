# Separate Cross-Model Handoff Condition

Ordinary retrieval over one conversation is not evidence of cross-model continuity. A separate condition should use two explicitly isolated stages:

1. Model A receives the source conversation and produces a transfer artifact under a fixed schema, without access to the gold state.
2. Model B receives only the transfer artifact plus the handoff task, not the source conversation, and reconstructs the state or answer.

Compare this condition with a source-conversation retrieval baseline and a no-transfer control. Keep cases, task text, context limits, and scoring identical. Report transfer-state fact preservation, stale-fact error rate, contradiction rate, unresolved-task accuracy, leakage checks, and answer quality separately from retrieval Recall@k. The transfer artifact must be logged for audit, and gold annotations must remain evaluator-only.

Do not describe the existing retrieval scripts as cross-model continuity evaluation; they measure diagnostic context selection only.

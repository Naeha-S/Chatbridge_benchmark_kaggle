# Semantic Validity Repair Report

The previous generator used explicit distractor cueing, independently sampled purportedly conflicting instructions, generic unresolved tasks, and no gold-state provenance. These were generator defects, not merely naming issues.

## Repairs

- Distractor conversations now contain neutral irrelevant facts without saying they are unrelated.
- Contradiction pairs are sampled as explicit incompatible instruction pairs, and validation checks the old/resolution semantics.
- Every expected active fact, constraint, unresolved task, and superseded item now has provenance with `source_grounded` or `permitted_inference` and source turn indices.
- Approval terminology no longer supplies article-prefixed values, avoiding constructions such as `The the ...`.
- Forgotten-fact cases receive longer variants with intervening context and competing information; direct source evidence remains available for objective scoring.
- A separate cross-model transfer condition is documented in `reports/handoff_condition_plan.md`; current retrieval evaluation is not relabeled as cross-model continuity.

## Regeneration comparison

Previous baseline measurements recorded in the Phase 1.5 audit: 84 cases, all with eight messages, one handoff task, one Friday-to-Monday update, one privacy instruction, one coffee-machine distractor, and two fixed unresolved tasks. The repaired generator uses multiple task patterns, 4–13 message conversations, multiple update and task-state patterns, and neutral distractor placement. Exact duplicate QA is checked after regeneration.

Automated checks are evidence of structural consistency only. They do not establish human semantic validity. All regenerated cases remain `unreviewed` until human review.

## Remaining issues

The generator is still synthetic and finite; repeated phrases and domain/template combinations remain possible. Human reviewers must inspect whether indirect forgotten facts are sufficiently difficult, whether every contradiction is realistically resolved, and whether permitted inferences are justified. The dataset must not be published or scaled before that review.


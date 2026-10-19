# Shortcut-Learning Audit: ContinuityBench v1

## Reproduction

Input: the generated 84-case JSONL produced with seed 7. The analysis normalized lowercase conversation text by replacing ticket IDs, project names, timezones, owner names, and then counted exact and near duplicates. A near-duplicate pair was counted when normalized token sequences differed in at most two aligned token positions and had length difference at most two. Token counts and family counts were computed with Python `Counter`. These are diagnostic measurements, not semantic judgments.

## Measured findings

- 84 cases were analyzed; exact normalized conversation duplicates: 0; unique normalized conversations: 84.
- Normalized near-duplicate pairs under the stated rule: 1,690 of 3,486 possible pairs (48.5%). This indicates highly repeated structure, although the rule is intentionally simple and may overcount.
- The most frequent normalized tokens include `is`, `in`, and `deadline` at 168 occurrences each; fixed conversational phrases such as `we are working on`, `owner`, and `i will track this` occur in all 84 cases.
- The generator has 4 project values, 3 timezones, 4 owner values, and 3 distractor templates.
- Every case contains `deadline moved to Monday`; 12 cases contain the `multi_failure` label.
- Scenario-family counts are 12 for each of the six single-failure families, plus 14 multi-failure families with counts from 1 to 2.
- The group split prevents family crossing, but families are still visibly shared structures within the dataset. The 84 cases are not independent natural conversations.
- Exact duplicate detection in the existing QA report found 0 pairs. This does not contradict the near-duplicate result because the QA key includes literal values and the near-duplicate analysis normalizes them.

## Heuristic baselines and leakage implications

A literal phrase heuristic can identify the temporal-update pattern because the same update wording appears in all 84 conversations. The `multi_failure` category is directly available in evaluator labels and must not be treated as model input; its occurrence in 12 cases demonstrates why label-derived features would be invalid. Project, owner, timezone, ticket formatting, and fixed turn wording provide potential memorization cues.

These are measured properties. The hypotheses that a model could predict scenario family or difficulty from wording, or that retrieval can exploit repeated fixed phrases rather than continuity reasoning, require a controlled model/heuristic experiment and are not claimed as measured performance here.

## Limitations

The audit does not estimate semantic similarity with embeddings, train a classifier, or measure performance on a genuinely unseen template. The near-duplicate threshold is lexical and can overcount benign similarities. It also does not establish whether any shortcut changes an end-to-end score. Human review remains required for semantic validity and ambiguity.

Conclusion: the dataset is useful for preliminary plumbing and regression tests, but its repeated templates make it unsuitable for claims about robust generalization.

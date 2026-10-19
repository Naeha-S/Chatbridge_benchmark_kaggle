# Held-Out-Template Evaluation Plan

Do not implement this experiment until the design is reviewed.

## Split design

Define a template family from the full generation structure: turn-role/order pattern, update wording pattern, task wording, distractor wording, and scenario composition. Assign a stable family ID before sampling. Partition entire families—not cases—into train, development, and held-out test. The held-out test must contain no family ID, paraphrase template, or shared phrase skeleton present in train/dev. If the current generator cannot provide at least one genuinely distinct family per split, the experiment must report that it is infeasible rather than relabeling existing variants.

## Construction

Create held-out cases by authoring new conversation and handoff templates with equivalent task semantics but different wording, turn order, distractor placement, and temporal-update phrasing. Keep the underlying evaluation dimensions and gold-state format fixed. Review all held-out gold states before scoring. Do not tune prompts, retrieval parameters, or heuristics on held-out cases.

## Fair evaluation

For every case, provide each baseline the identical `build_model_input` output, identical document/chunk boundaries, identical query, identical `k`, and identical context limit. Run no-retrieval, keyword, BM25, dense, and hybrid with the same deterministic settings. Record whether dense uses a real local embedding model or the deterministic offline fallback. Keep case order and tie-breaking deterministic.

## Metrics

Report retrieval Recall@k, irrelevant-context inclusion, context token count, and latency with per-case distributions—not only means. If an answer/state system is added later, report fact preservation, stale-fact error rate, contradiction rate, unresolved-task accuracy, and generated-answer quality separately. Include empty-denominator counts and confidence intervals or bootstrap intervals where sample size permits. Do not interpret retrieval metrics as conversational continuity quality.

## Poor-generalization criteria

Evidence of poor generalization includes a large held-out drop relative to development performance, near-zero recall for paraphrased required facts, increased stale or contradiction errors, increased distractor inclusion, or heuristic baselines matching model performance through template cues. Thresholds must be preregistered after inspecting only train/dev, not chosen after seeing held-out results.

The first comparison should be train/dev versus held-out-template test, followed by an ablation removing obvious lexical cues. Results should be labeled diagnostic until human review and end-to-end answer evaluation exist.

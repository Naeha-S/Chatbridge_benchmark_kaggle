# ContinuityBench v1 Schema

Each JSONL line is one case. `case_id` is stable. `source_conversation` is an ordered list of `{role, content}` turns. `handoff_task` is the model-facing task. `required_facts`, `required_constraints`, and `superseded_facts` are evaluator labels. `expected_continuity_state` is gold evaluator data and must not be supplied to evaluated models. `failure_categories`, `difficulty_level`, `scenario_types`, and `scenario_family_id` describe the case. `evaluation_criteria` contains evaluator annotations.

The published file preserves the repository's existing schema and values. It contains gold labels for reproducible evaluation; users must keep gold fields out of model prompts.

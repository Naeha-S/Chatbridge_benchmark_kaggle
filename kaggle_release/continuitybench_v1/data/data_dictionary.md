# Data Dictionary

| Field | Meaning | Model-facing? |
|---|---|---|
| `case_id` | Stable case identifier | No |
| `source_conversation` | Ordered source turns | Yes, through `build_model_input` |
| `handoff_task` | Handoff question/task | Yes |
| `required_facts` | Gold required facts | No |
| `required_constraints` | Gold constraints | No |
| `superseded_facts` | Gold historical facts | No |
| `irrelevant_distractor_facts` | Gold distractor annotations | No |
| `expected_continuity_state` | Gold state and provenance | No |
| `failure_categories` | Scenario labels | No |
| `difficulty_level` | Difficulty label | No |
| `evaluation_criteria` | Evaluator-only criteria | No |
| `scenario_types` | Scenario composition | No |
| `scenario_family_id` | Group split family | No |

The result CSV contains condition metrics and per-case differences. Retrieval evidence is intentionally excluded from the clean result CSV; it remains diagnostic-only in the source experiment manifest.

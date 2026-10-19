from __future__ import annotations

import random
from typing import Any

from .schema import SCHEMA_VERSION

SCENARIOS = [
    "forgotten_facts",
    "superseded_decisions",
    "contradictory_instructions",
    "temporal_changes",
    "unfinished_tasks",
    "irrelevant_context",
]


def _choose_scenarios(rng: random.Random, index: int) -> list[str]:
    if index % 7 == 6:
        picks = rng.sample(SCENARIOS, k=2)
        return picks + ["multi_failure"]
    return [SCENARIOS[index % len(SCENARIOS)]]


def generate_cases(count: int, seed: int = 7) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    cases: list[dict[str, Any]] = []
    for i in range(count):
        case_rng = random.Random(seed + i)
        scenarios = _choose_scenarios(case_rng, i)
        project = case_rng.choice(["alpha migration", "onboarding flow", "billing exporter", "forecast notebook"])
        timezone = case_rng.choice(["UTC", "PST", "CET"])
        owner = case_rng.choice(["Ari", "Jo", "Sam", "Rin"])
        ticket = f"TICKET-{seed}-{i:05d}"

        required_facts = [f"Project is {project}.", f"Owner is {owner}.", f"Tracking ticket is {ticket}."]
        required_constraints = ["Never expose customer email in outputs.", f"Use timezone {timezone} for deadlines."]

        superseded_facts = [{"old": "Initial note: deadline is Friday.", "new": "Update: deadline moved to Monday."}]
        distractors = [
            "Coffee machine in office was replaced.",
            "Team mascot is a penguin.",
            "Parking lot repainted last week.",
        ]

        conversation = [
            {"role": "user", "content": f"We are working on {project}."},
            {"role": "assistant", "content": f"Got it. Owner is {owner}."},
            {"role": "assistant", "content": f"I will track this under {ticket}."},
            {"role": "user", "content": "Do not include customer emails in summaries."},
            {"role": "user", "content": f"All deadlines should use {timezone}."},
            {"role": "user", "content": "Initial note: deadline is Friday."},
            {"role": "user", "content": "Update: deadline moved to Monday."},
            {"role": "user", "content": f"Also, {distractors[0]}"},
        ]

        handoff_task = "Continue the project and provide an action plan respecting constraints and updates."

        expected_state = {
            "active_facts": required_facts + ["Update: deadline moved to Monday."],
            "active_constraints": required_constraints,
            "unresolved_tasks": ["Prepare risk register", "Confirm deployment checklist"],
            "superseded": ["Initial note: deadline is Friday."],
        }

        case = {
            "schema_version": SCHEMA_VERSION,
            "case_id": f"CB-{i:05d}",
            "source_conversation": conversation,
            "handoff_task": handoff_task,
            "required_facts": required_facts,
            "required_constraints": required_constraints,
            "superseded_facts": superseded_facts,
            "irrelevant_distractor_facts": distractors,
            "expected_continuity_state": expected_state,
            "failure_categories": scenarios,
            "difficulty_level": case_rng.choice(["easy", "medium", "hard"]),
            "evaluation_criteria": {
                "must_preserve_required_facts": "true",
                "must_apply_latest_temporal_update": "true",
                "must_avoid_distractors": "true",
            },
            "scenario_types": scenarios,
        }
        cases.append(case)

    return cases

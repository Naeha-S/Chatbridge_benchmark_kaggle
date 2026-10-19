from __future__ import annotations

import random
from typing import Any, Callable

from .schema import SCHEMA_VERSION

SCENARIOS = ["forgotten_facts", "superseded_decisions", "contradictory_instructions", "temporal_changes", "unfinished_tasks", "irrelevant_context"]
DOMAINS = [
    ("clinic intake", "intake form", "Mina"),
    ("warehouse launch", "inventory sync", "Leo"),
    ("grant application", "budget packet", "Nia"),
    ("mobile release", "release candidate", "Omar"),
    ("school enrollment", "enrollment portal", "Priya"),
    ("research archive", "metadata index", "Quinn"),
]
DISTRACTORS = [
    "The office plants need watering.",
    "The team ordered new mugs.",
    "A neighboring team changed its logo.",
    "The elevator inspection is next week.",
    "The lunch menu includes soup today.",
    "The parking permits were reprinted.",
]

def _turn(role: str, text: str) -> dict[str, str]:
    return {"role": role, "content": text}


def _base(rng: random.Random) -> tuple[str, str, str, str]:
    domain, deliverable, owner = rng.choice(DOMAINS)
    return domain, deliverable, owner, f"CASE-{rng.randrange(100000, 999999)}"


def _forgotten(rng: random.Random) -> dict[str, Any]:
    domain, deliverable, owner, ref = _base(rng)
    channel = rng.choice(["the vendor portal", "the secure drive", "the intake queue"])
    fact = f"The {deliverable} must be submitted through {channel}."
    constraint = rng.choice(["Do not include patient identifiers in the handoff.", "Only the compliance lead may approve the final packet."])
    conversation = [_turn("user", f"We are preparing the {deliverable} for the {domain}."), _turn("assistant", f"I will coordinate with {owner}."), _turn("user", fact), _turn("user", constraint)]
    if rng.random() < 0.5:
        conversation.insert(1, _turn("user", f"The working reference is {ref}."))
    if rng.random() < 0.6:
        conversation = [conversation[0], _turn("user", "The kickoff notes mention a dependency review."), _turn("assistant", "I will check the open items."), _turn("user", "The reviewer asked for a concise handoff.")] + conversation[1:]
    return {"family": f"forgotten-route-v{rng.randrange(2)}", "conversation": conversation, "task": f"Continue the {domain} handoff and identify the submission route.", "facts": [f"The project concerns the {domain}.", fact], "constraints": [constraint], "active": [f"The project concerns the {domain}.", fact], "unresolved": [f"Confirm {deliverable} receipt"], "superseded": [], "distractors": [], "criteria": {"requires_retrieval": fact}}


def _superseded(rng: random.Random) -> dict[str, Any]:
    domain, deliverable, owner, _ = _base(rng)
    old = rng.choice(["design review", "legal review", "security review"])
    new = rng.choice(["accessibility review", "finance review", "operations review"])
    first = f"The {old} is the required approval for the {deliverable}."
    latest = f"The {new} replaces the {old} as the required approval."
    conversation = [_turn("user", f"For the {domain}, {first}"), _turn("assistant", f"I noted that {old} was required."), _turn("user", latest)]
    if rng.random() < 0.5:
        conversation.append(_turn("assistant", "I will use the latest approval rule."))
    return {"family": f"decision-replacement-v{rng.randrange(2)}", "conversation": conversation, "task": f"Prepare the {domain} handoff using the current approval rule.", "facts": [f"The project concerns the {domain}."], "constraints": [latest], "active": [f"The project concerns the {domain}.", latest], "unresolved": [], "superseded": [{"old": first, "new": latest}], "distractors": [], "criteria": {"requires_latest_decision": latest}}


def _contradictory(rng: random.Random) -> dict[str, Any]:
    domain, deliverable, owner, _ = _base(rng)
    old, resolution = rng.choice([("Publish the draft immediately.", "Hold publication until compliance approves it."), ("Share the report with the full mailing list.", "Share the report only with the review group."), ("Use production data in the example.", "Use synthetic data in the example.")])
    conversation = [_turn("user", f"We need the {deliverable} for the {domain}."), _turn("user", old), _turn("assistant", "I can prepare that."), _turn("user", resolution)]
    return {"family": f"instruction-conflict-v{rng.randrange(2)}", "conversation": conversation, "task": f"State the safe next step for the {domain} handoff.", "facts": [f"The project concerns the {domain}."], "constraints": [resolution], "active": [f"The project concerns the {domain}.", resolution], "unresolved": [f"Confirm {deliverable} is ready under the latest instruction"], "superseded": [], "distractors": [], "criteria": {"requires_resolution": resolution, "conflicts_with": old}}


def _temporal(rng: random.Random) -> dict[str, Any]:
    domain, deliverable, owner, _ = _base(rng)
    old_day, new_day = rng.choice([("Tuesday", "Thursday"), ("Friday", "Monday"), ("10 June", "17 June")])
    old = f"The {deliverable} deadline is {old_day}."
    new = f"The {deliverable} deadline moved to {new_day}."
    turns = [_turn("user", f"The {domain} is in progress."), _turn("user", old)]
    if rng.random() < 0.5:
        turns.append(_turn("user", "A dependency changed the schedule."))
    turns.extend([_turn("assistant", f"I recorded {old_day}."), _turn("user", new)])
    return {"family": f"schedule-update-v{rng.randrange(3)}", "conversation": turns, "task": f"Report the current deadline and identify which earlier deadline it superseded for the {domain}.", "facts": [f"The project concerns the {domain}."], "constraints": [new], "active": [f"The project concerns the {domain}.", new], "unresolved": [], "superseded": [{"old": old, "new": new}], "distractors": [], "criteria": {"requires_latest_value": new}}


def _unfinished(rng: random.Random) -> dict[str, Any]:
    domain, deliverable, owner, _ = _base(rng)
    pending = rng.choice([f"Obtain {deliverable} sign-off", f"Run the {deliverable} validation", f"Send the {deliverable} to the reviewer"])
    status = rng.choice(["pending", "blocked", "awaiting confirmation"])
    conversation = [_turn("user", f"The {domain} handoff has started."), _turn("assistant", f"The first draft is complete."), _turn("user", f"Next, {pending}; it is {status}."), _turn("assistant", "I will keep it on the handoff checklist.")]
    return {"family": f"task-state-v{rng.randrange(3)}", "conversation": conversation, "task": f"List what remains unresolved for the {domain}.", "facts": [f"The project concerns the {domain}."], "constraints": [], "active": [f"The project concerns the {domain}."], "unresolved": [f"{pending} ({status})"], "superseded": [], "distractors": [], "criteria": {"requires_unfinished_task": pending}}


def _irrelevant(rng: random.Random) -> dict[str, Any]:
    domain, deliverable, owner, _ = _base(rng)
    distractor = rng.choice(DISTRACTORS)
    conversation = [_turn("user", f"We need to finish the {deliverable} for the {domain}."), _turn("user", distractor), _turn("assistant", "I will keep the handoff focused on the requested deliverable."), _turn("user", f"The next step is to verify the {deliverable}.")]
    return {"family": f"distractor-placement-v{rng.randrange(3)}", "conversation": conversation, "task": f"Give the next relevant action for the {domain}.", "facts": [f"The project concerns the {domain}."], "constraints": [], "active": [f"The project concerns the {domain}."], "unresolved": [f"Verify the {deliverable}"], "superseded": [], "distractors": [distractor], "criteria": {"requires_ignore": distractor}}


BUILDERS: dict[str, Callable[[random.Random], dict[str, Any]]] = {"forgotten_facts": _forgotten, "superseded_decisions": _superseded, "contradictory_instructions": _contradictory, "temporal_changes": _temporal, "unfinished_tasks": _unfinished, "irrelevant_context": _irrelevant}


def _build_case(index: int, seed: int, rng: random.Random, scenarios: list[str]) -> dict[str, Any]:
    primary = BUILDERS[scenarios[0]](rng)
    if len(scenarios) == 1:
        data = primary
    else:
        secondary = BUILDERS[scenarios[1]](rng)
        data = {key: primary[key] for key in primary}
        data["family"] = f"composite-{primary['family']}+{secondary['family']}"
        data["conversation"] = primary["conversation"] + secondary["conversation"]
        data["task"] = primary["task"] + " Also resolve the second issue."
        data["facts"] = primary["facts"] + secondary["facts"]
        data["constraints"] = primary["constraints"] + secondary["constraints"]
        data["active"] = primary["active"] + [x for x in secondary["active"] if x not in primary["active"]]
        data["unresolved"] = primary["unresolved"] + secondary["unresolved"]
        data["superseded"] = primary["superseded"] + secondary["superseded"]
        data["distractors"] = primary["distractors"] + secondary["distractors"]
        data["criteria"] = {**primary["criteria"], **secondary["criteria"]}
    data["conversation"].append(_turn("assistant", f"Handoff reference: CB-{index:05d}."))
    difficulty = rng.choices(["easy", "medium", "hard"], weights=[3, 4, 3])[0]
    state = {"active_facts": data["active"], "active_constraints": data["constraints"], "unresolved_tasks": data["unresolved"], "superseded": [x["old"] for x in data["superseded"]]}
    text = [turn["content"] for turn in data["conversation"]]
    def evidence(item: str) -> dict[str, Any]:
        base = item.split(" (")[0]
        turns = [i for i, value in enumerate(text) if base.lower() in value.lower()]
        inferred = not turns
        return {"item": item, "evidence_type": "permitted_inference" if inferred else "source_grounded", "source_turns": turns or list(range(len(text))), "source_turn_ids": [f"turn-{i}" for i in (turns or list(range(len(text))))], "explanation": "Permitted inference: the item is derived from the cited conversation evidence." if inferred else "Directly stated or explicitly supported by the cited source turn(s)."}
    state["provenance"] = {"active_facts": [evidence(x) for x in data["active"]], "active_constraints": [evidence(x) for x in data["constraints"]], "unresolved_tasks": [evidence(x) for x in data["unresolved"]], "superseded": [{"item": x["old"], "evidence_type": "source_grounded", "source_turns": [i for i, value in enumerate(text) if x["old"].lower() in value.lower()], "source_turn_ids": [f"turn-{i}" for i, value in enumerate(text) if x["old"].lower() in value.lower()], "explanation": "Directly stated in the cited source turn."} for x in data["superseded"]]}
    return {"schema_version": SCHEMA_VERSION, "case_id": f"CB-{index:05d}", "source_conversation": data["conversation"], "handoff_task": data["task"], "required_facts": data["facts"], "required_constraints": data["constraints"], "superseded_facts": data["superseded"], "irrelevant_distractor_facts": data["distractors"], "expected_continuity_state": state, "failure_categories": scenarios, "difficulty_level": difficulty, "evaluation_criteria": data["criteria"], "scenario_types": scenarios, "scenario_family_id": data["family"]}


def generate_cases(count: int, seed: int = 7) -> list[dict[str, Any]]:
    cases = []
    for index in range(count):
        rng = random.Random(seed * 1009 + index * 9176)
        if index % 7 == 6:
            scenarios = rng.sample(SCENARIOS, 2) + ["multi_failure"]
        else:
            scenarios = [SCENARIOS[index % len(SCENARIOS)]]
        cases.append(_build_case(index, seed, rng, scenarios))
    return cases












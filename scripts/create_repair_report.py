from __future__ import annotations
import json
from pathlib import Path

def load(path): return {json.loads(line)["case_id"]: json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()}

def main():
    history = load("reports/generated/review_completed.jsonl")
    current = load("data/generated/continuitybench_v1.jsonl")
    corrected = [r for r in history.values() if r["review"]["status"] == "corrected" and r["review"]["reviewer"] == "Naeha" and r["review"]["review_date"] == "2026-10-19"]
    outcomes = []
    for old in corrected:
        new = current[old["case_id"]]
        before = old["gold_state"]
        after = new["expected_continuity_state"]
        outcomes.append({"case_id": old["case_id"], "historical_decision": "correct", "historical_reviewer": "Naeha", "historical_review_date": "2026-10-19", "repair_status": "awaiting_re_review", "before_gold_state": before, "after_gold_state": after, "gold_state_diff": {"unresolved_tasks_removed": sorted(set(before.get("unresolved_tasks", [])) - set(after.get("unresolved_tasks", []))), "unresolved_tasks_added": sorted(set(after.get("unresolved_tasks", [])) - set(before.get("unresolved_tasks", []))), "active_facts_changed": before.get("active_facts", []) != after.get("active_facts", []), "constraints_changed": before.get("active_constraints", []) != after.get("active_constraints", []), "superseded_changed": before.get("superseded", []) != after.get("superseded", [])}, "after_provenance": after.get("provenance", {}), "repair_note": old["review"]["correction_notes"]})
    report = {"source_history": "reports/generated/review_completed.jsonl", "total_cases": 84, "corrected_cases": len(outcomes), "new_cases_added": 0, "repair_status": "awaiting_re_review", "outcomes": outcomes, "remaining_unresolved_issues": ["Corrected cases have not been human re-reviewed.", "Accepted historical decisions remain historical and were not automatically changed.", "Automated checks do not establish semantic validity."]}
    Path("reports/generated/semantic_repair_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Semantic Repair Report", "", f"- Historical corrected cases: {len(outcomes)}", "- Dataset size after repair: 84", "- New cases added: 0", "- Repair status: awaiting re-review", "- Historical completed review artifacts were not overwritten.", "", "## Outcomes", ""]
    for item in outcomes:
        lines += [f"### {item['case_id']}", "", "- Historical decision: `correct`", "- Historical reviewer: `Naeha`", "- Repair status: `awaiting_re_review`", f"- Removed unresolved tasks: {item['gold_state_diff']['unresolved_tasks_removed'] or 'none'}", f"- Added unresolved tasks: {item['gold_state_diff']['unresolved_tasks_added'] or 'none'}", f"- Notes: {item['repair_note']}", ""]
    lines += ["## Remaining issues", "", "The repaired cases require a new human review. No case has been converted to accepted automatically. Automated QA and tests establish structural consistency only."]
    Path("reports/generated/semantic_repair_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"corrected_cases": len(outcomes), "new_cases_added": 0, "repair_status": "awaiting_re_review"}, indent=2))
if __name__ == "__main__": main()

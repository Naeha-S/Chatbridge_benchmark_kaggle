from __future__ import annotations
import argparse, json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter


def load(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def conversation_text(case):
    return "\n".join(f"{i + 1}. {turn['role'].upper()}: {turn['content']}" for i, turn in enumerate(case["source_conversation"]))


def state_text(case):
    state = case["expected_continuity_state"]
    return "\n".join([
        "ACTIVE FACTS:\n" + "\n".join(f"- {x}" for x in state.get("active_facts", [])),
        "ACTIVE CONSTRAINTS:\n" + "\n".join(f"- {x}" for x in state.get("active_constraints", [])),
        "UNRESOLVED TASKS:\n" + "\n".join(f"- {x}" for x in state.get("unresolved_tasks", [])),
        "SUPERSEDED:\n" + "\n".join(f"- {x}" for x in state.get("superseded", [])),
    ])


def make_markdown(cases, path):
    lines = ["# ContinuityBench Human Review Packet", "", "All 84 cases are evaluator-only review material. No decisions have been made. Set each case to accepted, corrected, or rejected only after reviewing the conversation against the gold state.", "", "## Decision labels", "", "- `accepted`: all checks pass and the gold state is supported.", "- `corrected`: the intended state is recoverable but an annotation needs a specific correction.", "- `rejected`: the state is ambiguous, unsupported, contradictory, or not objectively scorable.", "", "## Cases", ""]
    for n, case in enumerate(cases, 1):
        checks = case["expected_continuity_state"].get("provenance", {})
        lines += [f"### {n}. {case['case_id']}", "", f"- Scenario family: `{case.get('scenario_family_id')}`", f"- Categories: `{', '.join(case['failure_categories'])}`", f"- Difficulty: `{case['difficulty_level']}`", "", "**Handoff task**", "", case["handoff_task"], "", "**Source conversation**", "", "```text", conversation_text(case), "```", "", "**Gold state for review**", "", "```text", state_text(case), "```", "", "**Gold-state provenance**", "", "```json", json.dumps(checks, indent=2), "```", "", "**Reviewer entry**", "", "- Status: `unreviewed`", "- Reviewer decision:", "- Issue category:", "- Correction notes:", "", "---", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def make_workbook(cases, path):
    wb = Workbook()
    ws = wb.active; ws.title = "Case Review"
    headers = ["Case ID", "Scenario Family", "Categories", "Difficulty", "Conversation", "Handoff Task", "Gold State", "Provenance", "Temporal Updates Correct", "Stale Facts Correct", "Expected State Unambiguous", "Distractors Valid", "No Answer Leakage", "Status", "Reviewer Decision", "Issue Category", "Correction Notes"]
    ws.append(headers)
    for case in cases:
        ws.append([case["case_id"], case.get("scenario_family_id", ""), ", ".join(case["failure_categories"]), case["difficulty_level"], conversation_text(case), case["handoff_task"], state_text(case), json.dumps(case["expected_continuity_state"].get("provenance", {}), indent=2), "", "", "", "", "", "unreviewed", "", "none", ""])
    header_fill = PatternFill("solid", fgColor="1F4E78")
    for cell in ws[1]:
        cell.font = Font(color="FFFFFF", bold=True); cell.fill = header_fill; cell.alignment = Alignment(wrap_text=True, vertical="top")
    widths = [14, 30, 34, 12, 58, 48, 55, 50, 18, 18, 24, 18, 18, 14, 24, 26, 42]
    for i, width in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row[0].row].height = 120
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    for col in ("I", "J", "K", "L", "M"):
        DataValidation(type="list", formula1='",true,false"', allow_blank=True).add(f"{col}2:{col}{len(cases)+1}")
        dv = DataValidation(type="list", formula1='"true,false"', allow_blank=True); ws.add_data_validation(dv); dv.add(f"{col}2:{col}{len(cases)+1}")
    status = DataValidation(type="list", formula1='"unreviewed,accepted,corrected,rejected"', allow_blank=False); ws.add_data_validation(status); status.add(f"N2:N{len(cases)+1}")
    issue = DataValidation(type="list", formula1='"none,temporal_update,stale_fact,ambiguous_expected_state,invalid_distractor,answer_leakage,unsupported_state,other"', allow_blank=False); ws.add_data_validation(issue); issue.add(f"P2:P{len(cases)+1}")
    summary = wb.create_sheet("Summary")
    summary.append(["ContinuityBench Human Review Summary"]); summary.append([]); summary.append(["Total cases", len(cases)]); summary.append(["Unreviewed", f'=COUNTIF(\'Case Review\'!N:N,"unreviewed")']); summary.append(["Accepted", f'=COUNTIF(\'Case Review\'!N:N,"accepted")']); summary.append(["Corrected", f'=COUNTIF(\'Case Review\'!N:N,"corrected")']); summary.append(["Rejected", f'=COUNTIF(\'Case Review\'!N:N,"rejected")']); summary.append([]); summary.append(["Reminder", "Automated checks do not establish human semantic validity."])
    summary["A1"].font = Font(bold=True, size=14); summary.column_dimensions["A"].width = 28; summary.column_dimensions["B"].width = 70
    instructions = wb.create_sheet("Instructions")
    instruction_lines = ["Review each row in Case Review.", "1. Read the complete source conversation and handoff task.", "2. Compare the gold state with source evidence and provenance.", "3. Set every boolean check to true or false.", "4. Set Status to accepted, corrected, or rejected; leave unreviewed until actually reviewed.", "5. Record issue category and correction notes for corrected/rejected cases.", "Evaluator-only: do not provide this workbook or gold state to a model."]
    for line in instruction_lines: instructions.append([line])
    instructions.column_dimensions["A"].width = 120
    wb.save(path)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", required=True); parser.add_argument("--markdown", required=True); parser.add_argument("--xlsx", required=True); args = parser.parse_args()
    cases = load(args.dataset); make_markdown(cases, Path(args.markdown)); make_workbook(cases, Path(args.xlsx)); print(f"Markdown review packet -> {args.markdown}"); print(f"Excel review workbook -> {args.xlsx}")

if __name__ == "__main__": main()

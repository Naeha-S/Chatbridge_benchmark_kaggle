import json
from pathlib import Path
d=json.loads(Path("reports/generated/release_audit.json").read_text(encoding="utf-8"))
lines=["", "## Breakdown by category", "", "| Baseline | Category | Recall@5 | n |", "|---|---|---:|---:|"]
for name, data in d["baselines"].items():
    for cat, x in data["by_category"].items(): lines.append(f"| {name} | {cat} | {x['recall_at_5']:.4f} | {x['n']} |")
lines += ["", "## Breakdown by difficulty", "", "| Baseline | Difficulty | Recall@5 | n |", "|---|---|---:|---:|"]
for name, data in d["baselines"].items():
    for level, x in data["by_difficulty"].items(): lines.append(f"| {name} | {level} | {x['recall_at_5']:.4f} | {x['n']} |")
Path("reports/generated/release_audit.md").open("a", encoding="utf-8").write("\n".join(lines)+"\n")

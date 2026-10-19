from __future__ import annotations
import json, sys, importlib.util
from collections import defaultdict
from pathlib import Path
from statistics import mean
from continuitybench.metrics import context_size_tokens, irrelevant_inclusion_rate, retrieval_recall_at_k, timed_retrieval
from continuitybench.retrieval import BM25Retriever, DenseRetriever, HybridRetriever, KeywordRetriever, NoRetrievalBaseline
from continuitybench.schema import build_model_input
from continuitybench.quality import split_dataset

DATA = Path("data/generated/continuitybench_v1.jsonl")
OUT_JSON = Path("reports/generated/release_audit.json")
OUT_MD = Path("reports/generated/release_audit.md")
K = 5

def load(): return [json.loads(x) for x in DATA.read_text(encoding="utf-8").splitlines() if x.strip()]

def evaluate(factory, cases):
    rows=[]
    for case in cases:
        inp=build_model_input(case); docs=[turn["content"] for turn in inp["source_conversation"]]
        ret=factory(docs); ranked, latency=timed_retrieval(ret, inp["handoff_task"], K); selected=[x[1] for x in ranked]
        rows.append({"case_id":case["case_id"],"category":"+".join(case["failure_categories"]),"difficulty":case["difficulty_level"],"recall":retrieval_recall_at_k(case["required_facts"],selected),"irrelevant":irrelevant_inclusion_rate(selected,case["irrelevant_distractor_facts"]),"tokens":context_size_tokens(selected),"latency_ms":latency,"docs":len(docs),"query_in_docs":inp["handoff_task"].lower() in " ".join(docs).lower()})
    return rows

def summarize(rows):
    def agg(items): return {"n":len(items),"recall_at_5":mean(x["recall"] for x in items) if items else 0.0,"irrelevant_context_inclusion":mean(x["irrelevant"] for x in items) if items else 0.0,"context_size_tokens":mean(x["tokens"] for x in items) if items else 0.0,"latency_ms":mean(x["latency_ms"] for x in items) if items else 0.0}
    by_cat=defaultdict(list); by_diff=defaultdict(list)
    for row in rows: by_cat[row["category"]].append(row); by_diff[row["difficulty"]].append(row)
    return {"overall":agg(rows),"by_category":{k:agg(v) for k,v in sorted(by_cat.items())},"by_difficulty":{k:agg(v) for k,v in sorted(by_diff.items())}}

def main():
    cases=load(); factories={"no_retrieval":NoRetrievalBaseline,"keyword":KeywordRetriever,"bm25":BM25Retriever,"dense":DenseRetriever,"hybrid":HybridRetriever}
    results={}; backend={}
    for name,factory in factories.items():
        rows=evaluate(factory,cases); results[name]=summarize(rows)
        if name in {"dense","hybrid"}:
            probe=factory(["probe document"]); backend[name]={"sentence_transformers_installed":bool(importlib.util.find_spec("sentence_transformers")),"model_loaded":getattr(getattr(probe,"dense",probe),"_model",None) is not None,"fallback":"sha256 hashed bag-of-words"}
    splits=split_dataset(cases,seed=7); family_sets={k:{c["scenario_family_id"] for c in v} for k,v in splits.items()}
    input_keys=set(build_model_input(cases[0])); gold_keys=sorted(set(cases[0])-input_keys)
    report={"dataset":{"path":str(DATA),"count":len(cases),"seed":7,"k":K,"split_sizes":{k:len(v) for k,v in splits.items()}},"baselines":results,"backend":backend,"input_audit":{"model_input_keys":sorted(input_keys),"excluded_gold_or_evaluator_keys":gold_keys,"candidate_pool":"source conversation turns for the same case only","query":"handoff_task","relevance":"case-insensitive substring match of unique required_facts in concatenated selected documents"},"cross_model":{"plan_exists":Path("reports/handoff_condition_plan.md").exists(),"implementation_exists":Path("scripts/cross_model_handoff.py").exists(),"results_found":False},"limitations":["No end-to-end generated-answer or state-reconstruction metrics are implemented.","No cross-model handoff experiment has been run.","The current dense result uses the deterministic hash fallback, not a learned embedding model.","Per-category groups can be small, especially composite families.","Recall is text containment in selected source turns, not semantic relevance or answer quality."],"recommendation":"Not justified as a v0.1.0 research benchmark release; suitable only as a frozen, human-reviewed retrieval-scaffold artifact pending a cross-model experiment and stronger evaluation."}
    OUT_JSON.write_text(json.dumps(report,indent=2),encoding="utf-8")
    lines=["# ContinuityBench Release Audit","", "## Decision", "", "**v0.1.0 research benchmark release: not justified.** The frozen dataset and retrieval scaffold are reproducible and human-reviewed, but current results do not demonstrate cross-model continuity, end-to-end answer quality, or robust generalization.","", "## Aggregate retrieval results", "", "| Baseline | Recall@5 | Irrelevant inclusion | Context tokens | Latency ms | n |", "|---|---:|---:|---:|---:|---:|"]
    for name, data in results.items():
        x=data["overall"]; lines.append(f"| {name} | {x['recall_at_5']:.4f} | {x['irrelevant_context_inclusion']:.4f} | {x['context_size_tokens']:.2f} | {x['latency_ms']:.4f} | {x['n']} |")
    lines += ["", "## Interpretation", "", "Recall@5 is the number of unique required-fact strings found as case-insensitive substrings in the concatenated top-five source-turn documents, divided by unique required facts. It measures retrieval text containment only. Empty required-fact sets return 1.0. Irrelevant inclusion is distractor substring hits divided by distractors; empty distractor sets return 0.0. Fact preservation, stale-fact error, and contradiction rate are implemented utilities but were not evaluated by the retrieval CLI because no predicted states are produced.","", "The evaluator uses the handoff task as the query and the same case's source conversation turns as the candidate pool. Gold annotations are excluded from `build_model_input`. This is not a cross-model handoff condition and does not evaluate generated answers.","", "## Reproducibility and threats", "", f"Dataset count is {len(cases)}, seed 7, k=5, split sizes are { {k:len(v) for k,v in splits.items()} }. The dense backend did not load sentence-transformers in this environment and used the deterministic SHA-256 hashed bag-of-words fallback. The output does not record backend identity or dependency lock information, so this must be captured for any release.","", "The highest-priority threats are the lack of a run cross-model transfer experiment, lack of end-to-end answer/state metrics, substring relevance scoring, small category/family groups, and diagnostic retrieval scores being easy to overinterpret. These are validity limitations, not claims that the baselines are incorrect.","", "## Exact next experiment", "", "Run the documented two-stage handoff condition: Model A receives only `build_model_input` and emits a fixed transfer artifact; Model B receives only that artifact plus the handoff task. Compare against source-conversation retrieval and no-transfer controls on the same 84 cases, reporting fact preservation, stale-fact error, contradiction rate, unresolved-task accuracy, leakage checks, and answer quality. Use a preregistered split and record model identifiers, prompts, artifact schema, context limits, and backend versions."]
    OUT_MD.write_text("\n".join(lines),encoding="utf-8")
    print(f"Audit JSON -> {OUT_JSON}\nAudit Markdown -> {OUT_MD}")
if __name__ == "__main__": main()

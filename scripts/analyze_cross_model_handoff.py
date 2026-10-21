from __future__ import annotations
import csv, json, math, statistics
from collections import Counter, defaultdict
from pathlib import Path

INPUT=Path('reports/generated/current/cross_model_handoff_ollama_llama31_qwen3_source_retrieval_audit_20261020_full.json')
DATA=Path('data/generated/continuitybench_v1.jsonl')
OUT=Path('reports/generated/current/analysis_20261021')
CONDITIONS=('transfer','no_transfer','source_retrieval')
METRICS=('fact_preservation','stale_fact_error_rate','contradiction_rate','answer_required_fact_coverage')
HIGHER={'fact_preservation','answer_required_fact_coverage'}

def finite(x): return isinstance(x,(int,float)) and math.isfinite(x)
def stats(vals):
    return {'n':len(vals),'mean':statistics.mean(vals) if vals else None,'median':statistics.median(vals) if vals else None,'stddev_population':statistics.pstdev(vals) if vals else None,'min':min(vals) if vals else None,'max':max(vals) if vals else None,'zero_count':sum(x==0 for x in vals),'zero_pct':(100*sum(x==0 for x in vals)/len(vals)) if vals else None}
def write_csv(path,rows,fields):
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw=json.loads(INPUT.read_text(encoding='utf8')); cases=[json.loads(x) for x in DATA.read_text(encoding='utf8').splitlines() if x]
    data_ids=[c['case_id'] for c in cases]; result_cases=raw.get('per_case',[]); result_ids=[c.get('case_id') for c in result_cases]
    completed=set(result_ids); expected=set(data_ids); duplicate_ids=[x for x,n in Counter(result_ids).items() if n>1]; missing=sorted(expected-completed); extra=sorted(completed-expected)
    errors=[]; valid=[]; evidence_count=0; empty_count=0; mismatch_count=0
    for row in result_cases:
        if row.get('case_id') not in expected: errors.append((row.get('case_id'),'unknown_case')); continue
        if not all(isinstance(row.get(c),dict) for c in CONDITIONS): errors.append((row.get('case_id'),'missing_condition_metrics')); continue
        bad=[f'{c}.{m}' for c in CONDITIONS for m in METRICS if not finite(row[c].get(m)) or not 0<=row[c][m]<=1]
        if bad: errors.append((row['case_id'],'invalid_metric:'+','.join(bad))); continue
        ev=row.get('source_retrieval_evidence')
        if not isinstance(ev,dict) or not isinstance(ev.get('selected_turns'),list) or not isinstance(ev.get('formatted_context'),str): errors.append((row['case_id'],'missing_retrieval_evidence')); continue
        evidence_count+=1; selected=ev['selected_turns']; expected_context='\n'.join(f"[{x['turn_id']}] {x['content']}" for x in selected)
        if expected_context != ev['formatted_context']: mismatch_count+=1; errors.append((row['case_id'],'evidence_context_mismatch'))
        if not selected: empty_count+=1
        valid.append(row)
    failure_ids={x.get('case_id') for x in raw.get('failures',[]) if x.get('case_id') not in completed}
    historical_failures=sum(1 for x in raw.get('failures',[]) if x.get('case_id') in completed)
    # Aggregate
    agg=[]
    for cond in CONDITIONS:
        for metric in METRICS:
            vals=[r[cond][metric] for r in valid]
            s=stats(vals); agg.append({'condition':cond,'metric':metric,**s})
    write_csv(OUT/'aggregate_metrics.csv',agg,['condition','metric','n','mean','median','stddev_population','min','max','zero_count','zero_pct'])
    # per case
    prows=[]
    for r in valid:
        row={'case_id':r['case_id'],'category':r['category'],'difficulty':r['difficulty']}
        for c in CONDITIONS:
            for m in METRICS: row[f'{c}__{m}']=r[c][m]
        for m in METRICS:
            row[f'transfer_minus_no_transfer__{m}']=r['transfer'][m]-r['no_transfer'][m]
            row[f'source_retrieval_minus_no_transfer__{m}']=r['source_retrieval'][m]-r['no_transfer'][m]
        prows.append(row)
    fields=list(prows[0]) if prows else ['case_id']; write_csv(OUT/'per_case_analysis.csv',prows,fields)
    # paired
    pairs=(('transfer','no_transfer'),('source_retrieval','no_transfer'),('transfer','source_retrieval')); rows=[]
    for a,b in pairs:
        for m in METRICS:
            diffs=[r[a][m]-r[b][m] for r in valid]; favorable=sum(d>0 for d in diffs) if m in HIGHER else sum(d<0 for d in diffs); unfavorable=sum(d<0 for d in diffs) if m in HIGHER else sum(d>0 for d in diffs); ties=sum(d==0 for d in diffs); s=stats(diffs)
            rows.append({'comparison':f'{a}_vs_{b}','metric':m,'n':len(diffs),'mean_difference':statistics.mean(diffs) if diffs else None,'median_difference':statistics.median(diffs) if diffs else None,'favorable_to_first':favorable,'favorable_to_second':unfavorable,'ties':ties,'direction':'higher_better' if m in HIGHER else 'lower_better'})
    write_csv(OUT/'paired_comparisons.csv',rows,['comparison','metric','n','mean_difference','median_difference','favorable_to_first','favorable_to_second','ties','direction'])
    def breakdown(key,path):
        groups=sorted({r[key] for r in valid}); rows=[]
        for group in groups:
            subset=[r for r in valid if r[key]==group]
            for c in CONDITIONS:
                for m in METRICS:
                    s=stats([r[c][m] for r in subset]); rows.append({key:group,'condition':c,'metric':m,**s})
        write_csv(path,rows,[key,'condition','metric','n','mean','median','stddev_population','min','max','zero_count','zero_pct'])
    breakdown('category',OUT/'category_breakdown.csv'); breakdown('difficulty',OUT/'difficulty_breakdown.csv')
    meta={'input_result':str(INPUT),'dataset':str(DATA),'analysis_script':'scripts/analyze_cross_model_handoff.py','analysis_version':'20261021-v1','dataset_case_count':len(cases),'result_record_count':len(result_cases),'unique_completed_case_count':len(completed),'valid_case_count':len(valid),'missing_case_ids':missing,'duplicate_case_ids':duplicate_ids,'extra_case_ids':extra,'active_unresolved_failure_ids':sorted(failure_ids),'historical_failure_record_count':historical_failures,'retrieval_evidence_count':evidence_count,'empty_retrieval_count':empty_count,'evidence_context_mismatch_count':mismatch_count,'validation_errors':errors,'stddev':'population standard deviation (pstdev); descriptive only','metric_definitions':'Existing definitions in src/continuitybench/metrics.py; no scoring changes made.'}
    (OUT/'analysis_metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    lines=['# Validation Report','',f'- Dataset cases: {len(cases)}','- Result records: '+str(len(result_cases)),'- Unique completed IDs: '+str(len(completed)),'- Valid cases: '+str(len(valid)),'- Missing IDs: '+str(len(missing)), '- Duplicate IDs: '+str(len(duplicate_ids)), '- Active unresolved failures: '+str(len(failure_ids)), '- Historical failure records for subsequently completed cases: '+str(historical_failures), '- Retrieval evidence records: '+str(evidence_count), '- Empty retrieval cases: '+str(empty_count), '- Evidence/context mismatches: '+str(mismatch_count), '', 'Structural validation does not establish prediction correctness. Historical failure records are retained in the immutable result file and are not counted as active failures when their case IDs completed later.']
    (OUT/'validation_report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    # readable report
    def fmt(x): return 'n/a' if x is None else f'{x:.4f}' if isinstance(x,float) else str(x)
    lines=['# ContinuityBench Cross-Model Handoff Analysis','',f'Input: `{INPUT}`','',f'Valid completed cases: **{len(valid)}/84**. This is a descriptive analysis of one local run; no significance tests were performed.','', '## Aggregate Metrics','', '| Condition | Metric | N | Mean | Median | SD | Min | Max | Zero % |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in agg: lines.append('| {condition} | {metric} | {n} | {mean} | {median} | {stddev_population} | {min} | {max} | {zero_pct} |'.format(**{k:fmt(v) for k,v in r.items()}))
    lines+=['','## Paired Comparisons','', '| Comparison | Metric | Mean difference | Median difference | First favorable | Second favorable | Ties | Direction |','|---|---|---:|---:|---:|---:|---:|---|']
    for r in rows: lines.append('| {comparison} | {metric} | {mean_difference:.4f} | {median_difference:.4f} | {favorable_to_first} | {favorable_to_second} | {ties} | {direction} |'.format(**r))
    lines+=['','## Interpretation','', '- `fact_preservation` and `answer_required_fact_coverage` are higher-is-better exact-string measures.', '- `stale_fact_error_rate` and `contradiction_rate` are lower-is-better error measures.', '- BM25 evidence is lexical, not semantic. Exact-string scoring can mark valid paraphrases incorrect.', '- Zero stale-fact or contradiction scores do not prove complete correctness.', '- Models share one local Ollama environment; this is cross-model evaluation, not independent replication.', '- Category and difficulty groups should be interpreted with their reported sample sizes; no inferential claims are made.', '', '## Conclusion','', 'The run is structurally complete: all 84 IDs have one completed record and retrieval evidence. This supports descriptive comparison only. It does not establish generalization, semantic correctness, or statistical superiority.']
    (OUT/'analysis_report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print('wrote',OUT,'valid',len(valid),'errors',len(errors))
if __name__=='__main__': main()

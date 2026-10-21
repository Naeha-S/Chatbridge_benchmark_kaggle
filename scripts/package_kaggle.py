from __future__ import annotations
import argparse, csv, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/generated/continuitybench_v1.jsonl'
RESULT=ROOT/'reports/generated/current/analysis_20261021/per_case_analysis.csv'
ANALYSIS=ROOT/'reports/generated/current/analysis_20261021'
NOTEBOOK=ROOT/'kaggle/continuitybench_analysis.ipynb'
CC_LICENSE=ROOT/'kaggle/LICENSE-CC-BY-4.0.txt'


def load_ids(path):
    return [json.loads(line)['case_id'] for line in path.read_text(encoding='utf8').splitlines() if line.strip()]

def copy_file(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)

def main(argv=None):
    p=argparse.ArgumentParser(description='Build a temporary ContinuityBench Kaggle upload directory.')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--replace-existing',action='store_true',help='replace an existing disposable output directory')
    args=p.parse_args(argv); out=args.output
    if out.exists():
        if not args.replace_existing: raise SystemExit(f'refusing to overwrite existing output: {out}; use --replace-existing for a disposable directory')
        if out.resolve() in (ROOT,ROOT/'data',ROOT/'reports'): raise SystemExit('refusing unsafe output path')
        shutil.rmtree(out)
    dataset_ids=load_ids(DATA)
    with RESULT.open(encoding='utf8',newline='') as f: result_rows=list(csv.DictReader(f))
    result_ids=[r['case_id'] for r in result_rows]
    if len(dataset_ids)!=84 or len(set(dataset_ids))!=84: raise SystemExit('dataset validation failed: expected 84 unique case IDs')
    if len(result_ids)!=84 or set(result_ids)!=set(dataset_ids) or len(set(result_ids))!=84: raise SystemExit('result validation failed: expected one result row for every dataset case')
    required={'data/continuitybench_v1.jsonl':DATA,'data/README.md':ROOT/'data/README.md','results/per_case_results.csv':RESULT,'analysis/aggregate_metrics.csv':ANALYSIS/'aggregate_metrics.csv','analysis/paired_comparisons.csv':ANALYSIS/'paired_comparisons.csv','analysis/category_breakdown.csv':ANALYSIS/'category_breakdown.csv','analysis/difficulty_breakdown.csv':ANALYSIS/'difficulty_breakdown.csv','analysis/analysis_report.md':ANALYSIS/'analysis_report.md','analysis/validation_report.md':ANALYSIS/'validation_report.md','continuitybench_analysis.ipynb':NOTEBOOK,'README.md':ROOT/'kaggle/README.md','LICENSE_STATUS.md':ROOT/'kaggle/LICENSE_STATUS.md','LICENSE-CC-BY-4.0.txt':CC_LICENSE}
    for rel,src in required.items():
        if not src.exists(): raise SystemExit(f'missing canonical release source: {src}')
        copy_file(src,out/rel)
    manifest={'package_type':'temporary_kaggle_upload','case_count':84,'dataset_source':str(DATA.relative_to(ROOT)),'result_source':str(RESULT.relative_to(ROOT)),'diagnostic_manifest_excluded':True,'license_status':'CC BY 4.0 authorized by owner for the scoped original benchmark materials listed in LICENSE-CC-BY-4.0.txt; owner-provided authorization is not independent legal verification. Root MIT license remains limited to repository code.','owner_provided_provenance':{'statement':'Owner confirms all 84 benchmark conversations were generated specifically for ContinuityBench using ChatGPT/Codex and manually reviewed by the owner; to the owner''s knowledge, no third-party conversations or copied external material were used.','basis':'Owner-provided confirmation; not independently verified.','synthetic_provenance_and_non_confidentiality':'Requires owner confirmation and is not independently verified.'},'human_review_status':'Owner reports all 84 cases manually reviewed; review history is excluded from the minimal public package.','license_file_required_blocker':False,'publication_blockers':['Confirm redistribution terms for raw generated Llama 3.1 and Qwen3 outputs if they are ever released; they are excluded from this package.','Confirm that Kaggle metadata uses CC BY 4.0 for the scoped original benchmark materials and does not imply coverage of excluded materials.']}
    (out/'metadata').mkdir(parents=True,exist_ok=True); (out/'metadata/provenance.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(f'Created temporary upload directory: {out}')
    print('Validated 84 dataset IDs and 84 matching result rows; diagnostic manifest excluded.')
    return 0
if __name__=='__main__': raise SystemExit(main())





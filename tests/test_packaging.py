import json
from pathlib import Path
import pytest
import scripts.package_kaggle as pack

def test_packager_creates_valid_temporary_bundle_and_excludes_manifest():
    out=Path('kaggle_test_tmp_upload')
    if out.exists():
        import shutil; shutil.rmtree(out)
    try:
        assert pack.main(['--output',str(out)])==0
        assert sum(1 for _ in (out/'data/continuitybench_v1.jsonl').open(encoding='utf8'))==84
        assert sum(1 for _ in (out/'results/per_case_results.csv').open(encoding='utf8'))==85
        assert not (out/'metadata/source_experiment_manifest.json').exists()
        manifest=json.loads((out/'metadata/provenance.json').read_text(encoding='utf8'))
        assert manifest['diagnostic_manifest_excluded'] is True
        assert manifest['license_file_required_blocker'] is False
        assert manifest['publication_blockers']
        assert (out/'LICENSE-CC-BY-4.0.txt').exists()
    finally:
        if out.exists():
            import shutil; shutil.rmtree(out)

def test_packager_refuses_existing_output():
    out=Path('kaggle_test_existing_upload'); out.mkdir(exist_ok=True)
    try:
        with pytest.raises(SystemExit,match='refusing to overwrite'):
            pack.main(['--output',str(out)])
    finally:
        out.rmdir()




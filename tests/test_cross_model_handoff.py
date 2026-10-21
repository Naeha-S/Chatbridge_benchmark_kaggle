import json
import urllib.error
from pathlib import Path
import pytest
import scripts.cross_model_handoff as runner
class Resp:
    def __init__(self, body, headers=None): self.body=body; self.headers=headers or {'Content-Type':'application/json'}
    def __enter__(self): return self
    def __exit__(self,*a): pass
    def read(self): return self.body
def http_error(code, body=b'{"error":"quota"}', headers=None):
    return urllib.error.HTTPError('https://example.test',code,'x',headers or {},__import__('io').BytesIO(body))
def test_429_retries_and_honors_retry_after():
    calls=[]
    def opener(req,timeout):
        calls.append(1)
        if len(calls)==1: raise http_error(429,headers={'Retry-After':'3'})
        return Resp(b'{"ok":true}')
    delays=[]; result=runner.post('hf','https://example.test',{}, {},retries=2,opener=opener,sleeper=delays.append)
    assert result=={'ok':True}; assert delays==[3.0]; assert len(calls)==2
def test_402_does_not_retry():
    calls=[]
    def opener(req,timeout): calls.append(1); raise http_error(402,b'{"message":"credits required"}')
    with pytest.raises(runner.ProviderError) as exc: runner.post('hf','https://example.test',{}, {},retries=3,opener=opener,sleeper=lambda _:None)
    assert exc.value.kind=='billing_or_credits'; assert len(calls)==1; assert 'key' not in str(exc.value.record()).lower()
def test_malformed_and_empty_responses():
    with pytest.raises(runner.ProviderError) as exc: runner.post('gemini','https://example.test',{}, {},opener=lambda *a,**k:Resp(b'not json'))
    assert exc.value.kind=='invalid_json'
    with pytest.raises(runner.ProviderError) as exc: runner.post('gemini','https://example.test',{}, {},opener=lambda *a,**k:Resp(b''))
    assert exc.value.kind=='empty_response'
def test_ask_json_rejects_invalid_output():
    with pytest.raises(ValueError): runner.ask_json(lambda _: 'plain text','x')
    assert runner.ask_json(lambda _: '{"answer":"ok"}','x')['answer']=='ok'
def test_load_output_resume_does_not_duplicate():
    out=Path('reports/generated/current/continuitybench_handoff_test.json'); out.write_text(json.dumps({'per_case':[{'case_id':'CB-00000'}],'failures':[]}),encoding='utf8')
    loaded=runner.load_output(out); assert {x['case_id'] for x in loaded['per_case']}=={'CB-00000'}
    loaded['per_case'].append({'case_id':'CB-00001'}); runner.save_output(loaded,out)
    loaded2=runner.load_output(out); assert len(loaded2['per_case'])==2




def test_main_reports_all_skipped_and_returns_success(monkeypatch, capsys):
    data=Path('reports/generated/current/runner_test_cases.jsonl'); out=Path('reports/generated/current/runner_test_output.json')
    data.write_text('{"case_id":"CB-X"}\n',encoding='utf8'); out.write_text(json.dumps({'per_case':[{'case_id':'CB-X'}],'failures':[]}),encoding='utf8')
    monkeypatch.setattr(runner,'DATA',data); monkeypatch.setattr(runner,'OUT',out)
    assert runner.main([])==0
    text=capsys.readouterr().out; assert 'Skipped already-completed cases: 1' in text; assert 'no new comparisons' in text

def test_main_failure_returns_nonzero_and_reports_provider(monkeypatch, capsys):
    data=Path('reports/generated/current/runner_test_cases.jsonl'); out=Path('reports/generated/current/runner_test_output.json')
    data.write_text('{"case_id":"CB-Y"}\n',encoding='utf8'); out.write_text(json.dumps({'per_case':[],'failures':[]}),encoding='utf8')
    monkeypatch.setattr(runner,'DATA',data); monkeypatch.setattr(runner,'OUT',out); monkeypatch.setattr(runner,'build_model_input',lambda _: {'handoff_task':'x','source_conversation':[]})
    monkeypatch.setattr(runner,'gemini',lambda *a,**k: (_ for _ in ()).throw(runner.ProviderError('gemini','example.test','missing_credentials')))
    assert runner.main([])==2
    text=capsys.readouterr().out; assert 'Newly completed comparisons: 0' in text; assert 'gemini/missing_credentials: 1' in text

def test_main_invalid_case_id_returns_nonzero(monkeypatch, capsys):
    data=Path('reports/generated/current/runner_test_cases.jsonl'); monkeypatch.setattr(runner,'DATA',data)
    assert runner.main(['--case-id','CB-NOT-THERE'])==2
    assert 'case ID not found' in capsys.readouterr().out
def test_503_retries_then_succeeds_with_backoff():
    calls=[]
    def opener(req,timeout):
        calls.append(1)
        if len(calls)<3: raise http_error(503,b'{"error":"temporary"}',{'Retry-After':'2'})
        return Resp(b'{"ok":true}')
    delays=[]; assert runner.post('gemini','https://example.test',{}, {},retries=2,opener=opener,sleeper=delays.append)=={'ok':True}
    assert len(calls)==3 and delays==[2.0,2.0]
def test_503_exhausted_retries_records_final_error():
    calls=[]
    def opener(req,timeout): calls.append(1); raise http_error(503,b'{"message":"down"}')
    with pytest.raises(runner.ProviderError) as exc: runner.post('gemini','https://example.test',{}, {},retries=2,opener=opener,sleeper=lambda _:None,rng=lambda:0)
    assert len(calls)==3; assert exc.value.kind=='service_unavailable'; assert exc.value.status==503; assert exc.value.provider=='gemini'; assert exc.value.detail
def test_ollama_payload_and_response(monkeypatch):
    captured={}
    def fake_post(provider,url,headers,payload,**kwargs):
        captured.update({'provider':provider,'url':url,'payload':payload}); return {'message':{'content':'{"answer":"ok"}'}}
    monkeypatch.setattr(runner,'post',fake_post)
    monkeypatch.setenv('OLLAMA_BASE_URL','http://localhost:11434')
    assert runner.ollama_target('prompt',retries=0)=='{"answer":"ok"}'
    assert captured['url']=='http://localhost:11434/api/chat'; assert captured['payload']['model']=='qwen3:4b'; assert captured['payload']['stream'] is False; assert captured['payload']['format']=='json'; assert captured['payload']['think'] is False; assert captured['payload']['options']['temperature']==0

def test_ollama_output_is_separate():
    assert runner.output_path('ollama') != runner.output_path('legacy')
    assert runner.output_path('ollama').name=='cross_model_handoff_ollama_llama31_qwen3.json'
def test_normalize_structured_model_items_for_existing_metrics():
    pred={'active_facts':[{'fact':'current deadline is Monday'}], 'active_constraints':[], 'unresolved_tasks':[{'task':'send report'}], 'superseded':[{'text':'Friday deadline'}], 'contradicted_constraints':[], 'answer':'Monday'}
    normalized=runner.normalize_prediction(pred)
    assert normalized['active_facts']==['current deadline is Monday']; assert normalized['unresolved_tasks']==['send report']; assert normalized['superseded']==['Friday deadline']
    case={'required_facts':[],'required_constraints':[],'expected_continuity_state':{'active_facts':[],'superseded':[]}}
    assert runner.score(pred,case)['fact_preservation']==1.0
def test_source_retrieval_finds_late_relevant_turn_with_provenance():
    turns=[{'role':'user','content':'Old unrelated planning note'} for _ in range(5)] + [{'role':'user','turn_id':'turn-5','content':'The form must use the vendor portal for submission.'}]
    found=runner.retrieve_source_context(turns,'identify the submission route',k=3)
    assert found and found[0]['turn_id']=='turn-5'; assert found[0]['turn_index']==5

def test_source_retrieval_tie_breaks_by_original_order_and_handles_empty():
    turns=[{'role':'user','content':'submission route'}, {'role':'user','content':'submission route'}]
    found=runner.retrieve_source_context(turns,'submission route',k=2)
    assert [x['turn_index'] for x in found]==[0,1]
    assert runner.retrieve_source_context([], 'submission route')==[]
    assert runner.retrieve_source_context([{'content':'unrelated'}], 'missing term')==[]

def test_retrieved_prompt_contains_provenance_not_fixed_prefix():
    turns=[{'role':'user','content':'early unrelated'} for _ in range(5)] + [{'role':'user','content':'vendor portal submission route'}]
    context=runner.format_retrieved_context(runner.retrieve_source_context(turns,'submission route'))
    assert 'turn-5' in context and 'vendor portal' in context and 'early unrelated' not in context
def test_format_retrieved_context_uses_actual_newlines():
    retrieved=[{'turn_id':'turn-1','content':'first'},{'turn_id':'turn-2','content':'second'}]
    assert runner.format_retrieved_context(retrieved)=='[turn-1] first\n[turn-2] second'

def test_retrieval_evidence_persisted_and_matches_target_context(monkeypatch):
    source_case=json.loads(Path('data/generated/continuitybench_v1.jsonl').read_text(encoding='utf8').splitlines()[0])
    data=Path('reports/generated/current/_mock_retrieval_case.jsonl'); out=Path('reports/generated/current/_mock_retrieval_output.json')
    data.write_text(json.dumps(source_case)+'\n',encoding='utf8')
    calls=[]
    monkeypatch.setattr(runner,'DATA',data)
    monkeypatch.setattr(runner,'ollama_source',lambda prompt,**kw: '{"active_facts":[],"active_constraints":[],"unresolved_tasks":[],"superseded":[]}')
    def target(prompt,**kw): calls.append(prompt); return '{"active_facts":[],"active_constraints":[],"unresolved_tasks":[],"superseded":[],"answer":""}'
    monkeypatch.setattr(runner,'ollama_target',target)
    try:
        assert runner.main(['--backend','ollama_retrieval','--case-id','CB-00000','--output',str(out)])==0
        saved=json.loads(out.read_text(encoding='utf8'))['per_case'][0]
        evidence=saved['source_retrieval_evidence']
        assert evidence['selected_turns']==runner.retrieve_source_context(source_case['source_conversation'],source_case['handoff_task'])
        assert evidence['formatted_context']==runner.format_retrieved_context(evidence['selected_turns'])
        assert evidence['formatted_context'] in calls[-1]
    finally:
        data.unlink(missing_ok=True); out.unlink(missing_ok=True)

def test_empty_retrieval_evidence_is_explicit():
    assert runner.format_retrieved_context([])==''
def test_timeout_retries_and_becomes_structured_error():
    calls=[]
    def opener(req,timeout): calls.append(1); raise TimeoutError('ollama timed out')
    with pytest.raises(runner.ProviderError) as exc:
        runner.post('ollama:llama3.1:8b','http://localhost:11434/api/chat',{}, {},retries=2,opener=opener,sleeper=lambda _:None,rng=lambda:0)
    assert len(calls)==3; assert exc.value.kind=='network_timeout'; assert exc.value.provider=='ollama:llama3.1:8b'
def test_normalize_prediction_accepts_scalar_and_nested_structured_fields():
    pred={'active_facts':{'label':'clinic intake'},'active_constraints':[{'metadata':{'text':'no identifiers'}}],'unresolved_tasks':'confirm receipt','superseded':{'old':'Friday deadline'},'contradicted_constraints':[],'answer':{'text':'clinic intake'}}
    normalized=runner.normalize_prediction(pred)
    assert normalized['active_facts']==['clinic intake']; assert normalized['active_constraints']==['no identifiers']; assert normalized['unresolved_tasks']==['confirm receipt']; assert normalized['superseded']==['Friday deadline']; assert normalized['answer']=='clinic intake'

def test_normalize_prediction_omits_unreadable_items():
    assert runner.normalize_prediction({'active_facts':[{'metadata':{}}]})['active_facts']==[]
def test_start_case_id_selects_suffix(monkeypatch, capsys):
    data=Path('reports/generated/current/runner_test_cases.jsonl'); out=Path('reports/generated/current/runner_test_output.json')
    data.write_text('{"case_id":"CB-00000"}\n{"case_id":"CB-00059"}\n{"case_id":"CB-00060"}\n',encoding='utf8'); out.write_text(json.dumps({'per_case':[{'case_id':'CB-00059'},{'case_id':'CB-00060'}],'failures':[]}),encoding='utf8')
    monkeypatch.setattr(runner,'DATA',data); monkeypatch.setattr(runner,'OUT',out)
    try:
        assert runner.main(['--start-case-id','CB-00059'])==0
        text=capsys.readouterr().out; assert 'Selected cases: 2' in text; assert 'Skipped already-completed cases: 2' in text
    finally:
        data.unlink(missing_ok=True); out.unlink(missing_ok=True)

def test_missing_start_case_id_returns_nonzero(monkeypatch, capsys):
    data=Path('reports/generated/current/runner_test_cases.jsonl'); data.write_text('{"case_id":"CB-00000"}\n',encoding='utf8'); monkeypatch.setattr(runner,'DATA',data)
    try:
        assert runner.main(['--start-case-id','CB-NOPE'])==2; assert 'start case ID not found' in capsys.readouterr().out
    finally: data.unlink(missing_ok=True)

def test_retry_failures_selects_only_uncompleted_failure_ids(monkeypatch, capsys):
    data=Path('reports/generated/current/runner_test_cases.jsonl'); out=Path('reports/generated/current/runner_test_output.json')
    data.write_text('{"case_id":"CB-00001"}\n{"case_id":"CB-00002"}\n{"case_id":"CB-00003"}\n',encoding='utf8')
    out.write_text(json.dumps({'per_case':[{'case_id':'CB-00002'}],'failures':[{'case_id':'CB-00001','error':{'kind':'x'}},{'case_id':'CB-00002','error':{'kind':'x'}},{'case_id':'CB-00003','error':{'kind':'x'}}]}),encoding='utf8')
    monkeypatch.setattr(runner,'DATA',data); monkeypatch.setattr(runner,'OUT',out)
    try:
        assert runner.main(['--retry-failures'])==2
        text=capsys.readouterr().out; assert 'Selected cases: 2' in text
    finally: data.unlink(missing_ok=True); out.unlink(missing_ok=True)


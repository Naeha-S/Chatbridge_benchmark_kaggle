from __future__ import annotations
import argparse, json, os, random, time, socket, urllib.error, urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path
from continuitybench.metrics import contradiction_rate, fact_preservation, stale_fact_error_rate
from continuitybench.schema import build_model_input
from continuitybench.retrieval import BM25Retriever
DATA=Path('data/generated/continuitybench_v1.jsonl'); OUT=Path('reports/generated/current/cross_model_handoff_results.json'); OLLAMA_OUT=Path('reports/generated/current/cross_model_handoff_ollama_llama31_qwen3.json'); OLLAMA_RETRIEVAL_OUT=Path('reports/generated/current/cross_model_handoff_ollama_llama31_qwen3_source_retrieval.json'); SOURCE_RETRIEVAL_K=5
class ProviderError(RuntimeError):
    def __init__(self, provider, endpoint, kind, status=None, retry_after=None, detail=''):
        super().__init__(f'{provider}:{kind}' + (f':http_{status}' if status else '')); self.provider=provider; self.endpoint=endpoint; self.kind=kind; self.status=status; self.retry_after=retry_after; self.detail=detail
    def record(self):
        d={'provider':self.provider,'endpoint':self.endpoint,'kind':self.kind}
        if self.status is not None: d['status']=self.status
        if self.retry_after is not None: d['retry_after']=self.retry_after
        if self.detail: d['detail']=self.detail[:300]
        return d
def env_file():
    p=Path('.env')
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"\''))
def safe_body(raw):
    try:
        d=json.loads(raw.decode('utf-8',errors='replace'))
        if isinstance(d,dict):
            for k in ('key','token','authorization','access_token'): d.pop(k,None)
        return json.dumps(d,ensure_ascii=False)[:300]
    except Exception: return raw.decode('utf-8',errors='replace')[:300]
def post(provider,url,headers,payload,retries=2,backoff=1.0,opener=None,sleeper=time.sleep,rng=random.random):
    opener=opener or urllib.request.urlopen
    for attempt in range(retries+1):
        req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={**headers,'Content-Type':'application/json'},method='POST')
        try:
            with opener(req,timeout=90) as resp:
                raw=resp.read()
                if not raw: raise ProviderError(provider,url.split('?')[0],'empty_response')
                try: return json.loads(raw.decode('utf-8'))
                except json.JSONDecodeError as e: raise ProviderError(provider,url.split('?')[0],'invalid_json',detail=f'{resp.headers.get("Content-Type","")}:{e.msg}')
        except urllib.error.HTTPError as e:
            retry_after=e.headers.get('Retry-After') if e.headers else None; detail=safe_body(e.read())
            if e.code in (429, 503) and attempt<retries:
                delay=None
                if retry_after:
                    try: delay=float(retry_after)
                    except ValueError:
                        try: delay=max(0.0,(parsedate_to_datetime(retry_after).timestamp()-time.time()))
                        except (TypeError,ValueError,OverflowError): delay=None
                sleeper(delay if delay is not None else backoff*(2**attempt)+rng()*.25); continue
            kind='rate_limited' if e.code==429 else 'service_unavailable' if e.code==503 else 'billing_or_credits' if e.code==402 else 'http_error'
            raise ProviderError(provider,url.split('?')[0],kind,e.code,retry_after,detail)
        except (TimeoutError, socket.timeout) as e:
            if attempt<retries: sleeper(backoff*(2**attempt)+rng()*.25); continue
            raise ProviderError(provider,url.split('?')[0],'network_timeout',detail=str(e))
        except urllib.error.URLError as e:
            if attempt<retries: sleeper(backoff*(2**attempt)+rng()*.25); continue
            raise ProviderError(provider,url.split('?')[0],'network_error',detail=str(e.reason))
def gemini(prompt,**kw):
    model=os.environ.get('GEMINI_MODEL','gemini-2.5-flash'); key=os.environ.get('GEMINI_API_KEY')
    if not key: raise ProviderError('gemini','generativelanguage.googleapis.com','missing_credentials')
    url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
    d=post('gemini',url,{}, {'contents':[{'role':'user','parts':[{'text':prompt}]}],'generationConfig':{'temperature':0,'responseMimeType':'application/json'}},**kw)
    try: return d['candidates'][0]['content']['parts'][0]['text']
    except (KeyError,IndexError,TypeError): raise ProviderError('gemini',url.split('?')[0],'unexpected_response')
def hf(prompt,**kw):
    model=os.environ.get('HF_MODEL','meta-llama/Llama-3.1-8B-Instruct'); token=os.environ.get('HF_TOKEN')
    if not token: raise ProviderError('huggingface','router.huggingface.co/v1/chat/completions','missing_credentials')
    url='https://router.huggingface.co/v1/chat/completions'; d=post('huggingface',url,{'Authorization':f'Bearer {token}'},{'model':model,'messages':[{'role':'user','content':prompt}],'temperature':0,'max_tokens':1200},**kw)
    try: return d['choices'][0]['message']['content']
    except (KeyError,IndexError,TypeError): raise ProviderError('huggingface',url,'unexpected_response')
def ollama(prompt, model, think=False, **kw):
    base=os.environ.get('OLLAMA_BASE_URL','http://localhost:11434').rstrip('/')
    url=base+'/api/chat'
    payload={'model':model,'messages':[{'role':'user','content':prompt}],'stream':False,'format':'json','options':{'temperature':0,'repeat_penalty':float(os.environ.get('OLLAMA_REPEAT_PENALTY','1.1')),'num_predict':int(os.environ.get('OLLAMA_NUM_PREDICT','800'))}}
    payload['think']=think
    data=post('ollama:'+model,url,{},payload,**kw)
    try:
        content=data['message']['content']
    except (KeyError,TypeError):
        raise ProviderError('ollama:'+model,url,'unexpected_response',detail='missing message/content')
    if not content: raise ProviderError('ollama:'+model,url,'empty_model_content')
    return content

def ollama_source(prompt, **kw):
    return ollama(prompt, os.environ.get('OLLAMA_SOURCE_MODEL','llama3.1:8b'), think=False, **kw)

def ollama_target(prompt, **kw):
    return ollama(prompt, os.environ.get('OLLAMA_TARGET_MODEL','qwen3:4b'), think=False, **kw)

def output_path(backend):
    return OLLAMA_RETRIEVAL_OUT if backend == 'ollama_retrieval' else OLLAMA_OUT if backend == 'ollama' else OUT
def ask_json(provider,prompt):
    raw=provider(prompt)
    if not isinstance(raw,str): raise ValueError('model output was not text')
    a,b=raw.find('{'),raw.rfind('}')
    if a<0 or b<a: raise ValueError('model output contained no JSON object')
    try: value=json.loads(raw[a:b+1])
    except json.JSONDecodeError as e: raise ValueError(f'model JSON parse failure: {e.msg}')
    if not isinstance(value,dict): raise ValueError('model JSON was not an object')
    return value
def retrieve_source_context(source_conversation, query, k=SOURCE_RETRIEVAL_K):
    documents=[turn.get('content','') for turn in source_conversation]
    if not documents or not query or k <= 0: return []
    ranked=BM25Retriever(documents).retrieve(query,k=min(k,len(documents)))
    relevant=[item for item in ranked if item[2] > 0.0]
    selected=[]
    for index, content, score_value in relevant:
        turn=source_conversation[index]
        turn_id=turn.get('turn_id',f'turn-{index}')
        selected.append({'turn_id':turn_id,'turn_index':index,'content':content,'score':score_value})
    return selected

def format_retrieved_context(retrieved):
    return '\n'.join(f"[{item['turn_id']}] {item['content']}" for item in retrieved)
def artifact_prompt(inp): return 'Return JSON with active_facts, active_constraints, unresolved_tasks, superseded, and transfer_summary. Use only this task and conversation; omit unsupported facts.\nTASK:\n'+inp['handoff_task']+'\nCONVERSATION:\n'+json.dumps(inp['source_conversation'],ensure_ascii=False)
def model_b_prompt(task,context): return 'Return JSON with active_facts, active_constraints, unresolved_tasks, superseded, and answer. Use only supplied context; do not invent tasks.\nTASK:\n'+task+'\nCONTEXT:\n'+context
def _text_from_item(value):
    if isinstance(value,str): return value
    if not isinstance(value,dict): return None
    for key in ('fact','constraint','task','text','content','value','item','old','new','description','name'):
        candidate=value.get(key)
        if isinstance(candidate,str) and candidate.strip(): return candidate
    leaves=[]
    def collect(item):
        if isinstance(item,str) and item.strip(): leaves.append(item)
        elif isinstance(item,dict):
            for child in item.values(): collect(child)
        elif isinstance(item,list):
            for child in item: collect(child)
    collect(value)
    return ' | '.join(leaves) if leaves else None

def normalize_prediction(pred):
    if not isinstance(pred,dict): raise ValueError('model prediction must be an object')
    normalized=dict(pred)
    fields=('active_facts','active_constraints','unresolved_tasks','superseded','contradicted_constraints')
    for field in fields:
        values=normalized.get(field,[])
        if values is None: values=[]
        if isinstance(values,dict): values=[values]
        elif isinstance(values,str): values=[values]
        if not isinstance(values,list): values=[values]
        clean=[]
        for value in values:
            text=_text_from_item(value)
            if text is None: continue
            clean.append(text)
        normalized[field]=clean
    if 'answer' in normalized and not isinstance(normalized['answer'],str):
        normalized['answer']=_text_from_item(normalized['answer']) or ''
    return normalized
def score(pred,case):
    pred=normalize_prediction(pred)
    required=case['required_facts']; return {'fact_preservation':fact_preservation(pred,case['expected_continuity_state']),'stale_fact_error_rate':stale_fact_error_rate(pred,case['expected_continuity_state']),'contradiction_rate':contradiction_rate(pred,case['required_constraints']),'answer_required_fact_coverage':sum(f.lower() in pred.get('answer','').lower() for f in required)/len(set(required)) if required else 1.0}
def load_output(path=None):
    path = path or OUT
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'per_case': [], 'failures': []}

def save_output(output, path=None):
    path = path or OUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--case-id')
    parser.add_argument('--retry-failures',action='store_true', help='retry case IDs recorded as failures in the selected output')
    parser.add_argument('--start-case-id', help='start at this dataset case ID and continue through the selected range')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--retries',type=int,default=int(os.environ.get('CB_RETRIES','2')))
    parser.add_argument('--backend',choices=['legacy','ollama','ollama_retrieval'],default=os.environ.get('CB_BACKEND','legacy'))
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv); env_file()
    all_cases=[json.loads(x) for x in DATA.read_text(encoding='utf-8').splitlines() if x]
    path=args.output or output_path(args.backend); out=load_output(path); done={x['case_id'] for x in out.get('per_case',[])}
    if args.case_id:
        cases=[c for c in all_cases if c['case_id']==args.case_id]
        if not cases:
            print(f'ERROR: case ID not found: {args.case_id}')
            return 2
    else: cases=all_cases
    if args.retry_failures:
        failed_ids={x.get('case_id') for x in out.get('failures',[]) if x.get('case_id') not in done}
        cases=[c for c in cases if c['case_id'] in failed_ids]
    if args.start_case_id:
        start_ids=[i for i,c in enumerate(cases) if c['case_id']==args.start_case_id]
        if not start_ids:
            print(f'ERROR: start case ID not found: {args.start_case_id}')
            return 2
        cases=cases[start_ids[0]:]
    if args.limit: cases=cases[:args.limit]
    selected=len(cases); skipped=sum(c['case_id'] in done for c in cases); attempted=0; new_completed=0; failures=[]
    for case in cases:
        if case['case_id'] in done: continue
        attempted+=1
        try:
            inp=build_model_input(case)
            source_fn=ollama_source if args.backend in ('ollama','ollama_retrieval') else gemini
            target_fn=ollama_target if args.backend in ('ollama','ollama_retrieval') else hf
            art=ask_json(lambda x: source_fn(x, retries=args.retries), artifact_prompt(inp))
            task=inp['handoff_task']
            transfer=ask_json(lambda x: target_fn(x, retries=args.retries), model_b_prompt(task, json.dumps(art)))
            no=ask_json(lambda x: target_fn(x, retries=args.retries), model_b_prompt(task, ''))
            retrieval_evidence=None
            if args.backend=='ollama_retrieval':
                retrieved=retrieve_source_context(inp['source_conversation'], task)
                retrieval_context=format_retrieved_context(retrieved)
                retrieval_evidence={'selected_turns':retrieved,'formatted_context':retrieval_context}
                source_prompt=model_b_prompt(task, retrieval_context)
            else:
                source_prompt=model_b_prompt(task, '\n'.join(x['content'] for x in inp['source_conversation'][:5]))
            src=ask_json(lambda x: target_fn(x, retries=args.retries), source_prompt)
            record={'case_id':case['case_id'],'category':'+'.join(case['failure_categories']),'difficulty':case['difficulty_level'],'transfer':score(transfer,case),'no_transfer':score(no,case),'source_retrieval':score(src,case),'artifact':art}
            if retrieval_evidence is not None: record['source_retrieval_evidence']=retrieval_evidence
            out['per_case'].append(record); done.add(case['case_id']); new_completed+=1
        except ProviderError as e:
            failure={'case_id':case['case_id'],'error':e.record()}
            if not any(x.get('case_id')==case['case_id'] and x.get('error')==failure['error'] for x in out.setdefault('failures',[])):
                out['failures'].append(failure)
            failures.append(failure)
        except (ValueError,KeyError,IndexError,TypeError) as e:
            failure={'case_id':case['case_id'],'error':{'kind':'parse_or_schema_error','detail':str(e)[:300]}}
            if not any(x.get('case_id')==case['case_id'] and x.get('error')==failure['error'] for x in out.setdefault('failures',[])):
                out['failures'].append(failure)
            failures.append(failure)
        save_output(out,path)
    out.update({'dataset':str(DATA),'num_cases':len(all_cases),'completed_cases':len(out['per_case']),'backend':args.backend,'source_retrieval_k':SOURCE_RETRIEVAL_K if args.backend=='ollama_retrieval' else None,'models':({'model_a':'Ollama '+os.environ.get('OLLAMA_SOURCE_MODEL','llama3.1:8b'),'model_b':'Ollama '+os.environ.get('OLLAMA_TARGET_MODEL','qwen3:4b')} if args.backend in ('ollama','ollama_retrieval') else {'model_a':'Gemini '+os.environ.get('GEMINI_MODEL','gemini-2.5-flash'),'model_b':'HuggingFace '+os.environ.get('HF_MODEL','meta-llama/Llama-3.1-8B-Instruct')})}); save_output(out,path)
    from collections import Counter
    kinds=Counter((f.get('error',{}).get('kind','unknown'),f.get('error',{}).get('provider','unknown')) for f in failures)
    print(f'Selected cases: {selected}')
    print(f'Newly completed comparisons: {new_completed}')
    print(f'Skipped already-completed cases: {skipped}')
    print(f'Failures this invocation: {len(failures)}')
    for (kind,provider),count in sorted(kinds.items()): print(f'  {provider}/{kind}: {count}')
    if selected and skipped==selected and not failures: print('All selected cases were already completed; no new comparisons were run.')
    if new_completed==0 and attempted>0: return 2
    return 0
if __name__=='__main__': raise SystemExit(main())














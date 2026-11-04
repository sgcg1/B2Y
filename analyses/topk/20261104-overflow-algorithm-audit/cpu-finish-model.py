"""Read-only CPU execution of actual finish AST: logical work, not NPU timing."""
import ast, contextlib, importlib.util, json, sys, struct, hashlib
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
helpers=load(ROOT/'tests/kernels/test_topk_select_decode_pipeline_ascend.py','helpers')
cases=load(Path('D:/04_Project/B2Y/diagnostics/topk-formal-decode-r14/cases.py'),'cases')
tree=ast.parse((ROOT/'src/tileops/_kernels/attention/topk_select_decode_pipeline_ascend.py').read_text())
func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='decode_finish')
main=next(n for n in func.body if isinstance(n,ast.FunctionDef) and n.name=='main')
class Lower(ast.NodeTransformer):
    def __init__(self):self.lane=0
    def visit_Call(self,node):
        if ast.unparse(node.func)=='T.atomic_add':
            target=node.args[0]
            return ast.Call(func=ast.Name(id='add',ctx=ast.Load()),args=[target.value,target.slice,node.args[1]],keywords=node.keywords)
        return self.generic_visit(node)
    def visit_For(self,node):
        node=self.generic_visit(node)
        if isinstance(node.target,ast.Name) and node.target.id=='round':
            node.body=[ast.parse('begin_round(round)').body[0]]+node.body+[ast.parse('end_round(round)').body[0]]
        if isinstance(node.target,ast.Name) and node.target.id=='lane':
            kind='hist' if self.lane==0 else 'emit';self.lane+=1
            node.body=[ast.parse('slot("'+kind+'")').body[0]]+node.body
        return node
code=compile(ast.fix_missing_locations(Lower().visit(ast.Module(body=main.body,type_ignores=[]))),'actual-finish','exec')
def simulate(spec):
    values=[struct.unpack('f',struct.pack('f',v))[0] for v in spec['values']];start,stop=spec['window'];N=len(values);K=2048
    coarse=[helpers.coarse(v) for v in values];hist=[0]*256
    for i in range(start,stop):hist[coarse[i]]+=1
    before=0;threshold=-1;boundary=0
    for b in range(255,-1,-1):
        if before<=K<before+hist[b]:threshold=b;boundary=hist[b];break
        before+=hist[b]
    if threshold<0:before=max(0,stop-start)
    accepted=[i for i in range(start,stop) if coarse[i]>threshold]
    pending=[i for i in range(start,stop) if coarse[i]==threshold]
    out=accepted+[N]*(K-len(accepted));pending=pending[:K]
    counters=dict(hist_slots=0,emit_slots=0,hist_atomics=0,output_atomics=0,score_calls=0,coarse_calls=0,vf_calls=0)
    rounds=[];snapshot={};bins={}
    def score(v):counters['score_calls']+=1;return helpers.score(v)
    def coarse_fn(v):counters['coarse_calls']+=1;return helpers.coarse(v)
    def add(array,i,value,return_prev=False):
        old=array[i];array[i]+=value
        if return_prev:counters['output_atomics']+=1
        else:
            counters['hist_atomics']+=1;bins[i]=bins.get(i,0)+1
        return old
    def slot(kind):counters[kind+'_slots']+=1
    def begin_round(r):
        snapshot.clear();snapshot.update(counters);bins.clear();snapshot['quota']=env['state'][0]
    def end_round(r):
        rounds.append(dict(round=r,quota_before=snapshot['quota'],quota_after=env['state'][0],accepted=env['state'][3],
            hist_slots=counters['hist_slots']-snapshot['hist_slots'],emit_slots=counters['emit_slots']-snapshot['emit_slots'],
            hist_atomics=counters['hist_atomics']-snapshot['hist_atomics'],peak_hist_bin=max(bins.values(),default=0),
            vf_calls=counters['vf_calls']-snapshot['vf_calls']))
    def vf(**kwargs):counters['vf_calls']+=1;return contextlib.nullcontext()
    lang=SimpleNamespace(Kernel=lambda *args:contextlib.nullcontext(),SimtVF=vf,Parallel=range,serial=range,
        alloc_shared=lambda shape,dtype:[0]*shape[0],alloc_var=lambda dtype:0,int32='int32',uint32='uint32',float32='float32',
        Cast=lambda dtype,x:int(x)&0xffffffff if dtype=='uint32' else float(x) if dtype=='float32' else int(x),
        copy=lambda source,target:target.__setitem__(slice(None),source),if_then_else=lambda c,a,b:a if c else b,
        max=max,min=min,ceildiv=lambda a,b:(a+b-1)//b)
    env=dict(T=lang,STABLE_TIE=False,ADAPTIVE_TIE=True,EARLY_EXIT=True,FUSE_QUOTA=False,SKIP_INDEX_PREFIX=False,
        STAGE_OVERFLOW=True,CACHE_OVERFLOW_KEYS=True,CACHE_OVERFLOW_COARSE=True,WINDOW_PRECOMPUTE=True,
        x=values,starts=[start],ends=[stop],meta=[threshold,before,boundary,stop-start],candidate_scores=[values[i] for i in pending]+[0.]*(K-len(pending)),
        candidate_indices=pending+[0]*(K-len(pending)),out=out,final_state=[-1,-1],score_key=score,coarse_byte=coarse_fn,
        add=add,slot=slot,begin_round=begin_round,end_round=end_round)
    exec(code,env)
    expected=sorted(range(start,stop),key=lambda i:(helpers.score(values[i]),-i),reverse=True)[:K]
    assert sorted(env['out'])==sorted(expected),spec['label']
    assert env['final_state']==[0,K]
    return dict(label=spec['label'],input_sha256=hashlib.sha256(b''.join(struct.pack('f',v) for v in values)).hexdigest(),window=[start,stop],coarse_boundary=boundary,accepted_initial=before,
                pending_quota=K-before,logical_counts=counters,rounds=rounds,exact_set_passed=True)
if __name__=='__main__':
    selected=[c for c in cases.build_cases() if c['label'] in ['random-control','boundary-2048','boundary-2049','quantized-four-levels','close-fp32','narrow-overflow']]
    selected.append(dict(label='all-equal',values=[1.]*16384,window=[0,16384]))
    result=[simulate(c) for c in selected]
    path=ROOT/'artifacts/topk_algorithm_work_counts.json';path.write_text(json.dumps(result,indent=2)+'\n')
    for row in result:print(json.dumps(row))

"""Execute the actual new kernel AST on CPU; no TileLang or NPU imports."""
import ast
import contextlib
import json
from pathlib import Path
from types import SimpleNamespace
from cases import build_cases,expected,signed,L,K


class Tensor:
    def __init__(self,rows,track=False):
        self.rows=rows
        self.writes={} if track else None
    def __getitem__(self,key):
        indices=key if isinstance(key,tuple) else (key,)
        value=self.rows
        for i in indices:
            assert 0<=i<len(value),(key,len(value))
            value=value[i]
        return value
    def __setitem__(self,key,value):
        indices=key if isinstance(key,tuple) else (key,)
        target=self.rows
        for i in indices[:-1]:
            assert 0<=i<len(target),key
            target=target[i]
        assert 0<=indices[-1]<len(target),key
        target[indices[-1]]=value
        if self.writes is not None:self.writes[indices]=self.writes.get(indices,0)+1


def validate():
    root=Path(__file__).resolve().parent
    source=ast.parse((root/"kernels.py").read_text(encoding="utf-8"))
    fn=next(x for x in source.body if isinstance(x,ast.FunctionDef) and x.name=="merge_batches")
    main=next(x for x in fn.body if isinstance(x,ast.FunctionDef) and x.name=="main")
    code=compile(ast.fix_missing_locations(ast.Module(body=main.body,type_ignores=[])),"actual-merge-kernel","exec")
    cases=build_cases();B=len(cases)
    keys=Tensor([[[signed(k) for k,i in c[side]]+[0]*(L-len(c[side])) for side in ("left","right")] for c in cases])
    ids=Tensor([[[i for k,i in c[side]]+[0]*(L-len(c[side])) for side in ("left","right")] for c in cases])
    lengths=Tensor([[len(c['left']),len(c['right'])] for c in cases])
    limits=Tensor([c['limit'] for c in cases])
    for R in (128,256):
        out_key=Tensor([[-1]*K for _ in cases],True)
        out_id=Tensor([[-1]*K for _ in cases],True)
        trace=Tensor([[[-1]*3 for _ in range(K//R)] for _ in cases])
        for worker,case in enumerate(cases):
            lang=SimpleNamespace(Kernel=lambda *args:contextlib.nullcontext(worker),SimtVF=lambda **kwargs:contextlib.nullcontext(),
                alloc_shared=lambda shape,dtype:[0]*shape[0],alloc_var=lambda dtype:0,
                Parallel=range,serial=range,int32='int32',uint32='uint32',min=min,
                if_then_else=lambda c,a,b:a if c else b,reinterpret=lambda v,d:v&0xffffffff)
            env=dict(T=lang,B=B,R=R,L=L,K=K,STEPS=R.bit_length(),keys=keys,ids=ids,lengths=lengths,limits=limits,out_key=out_key,out_id=out_id,trace=trace)
            exec(code,env)
            want_key,want_id,want_trace=expected(case,R)
            assert out_key.rows[worker]==[signed(k) for k in want_key],(R,case['name'],'keys')
            assert out_id.rows[worker]==want_id,(R,case['name'],'ids')
            assert trace.rows[worker]==want_trace,(R,case['name'],'trace')
            for j in range(K):
                count=2 if j<len(case['oracle']) else 1
                assert out_id.writes[(worker,j)]==out_key.writes[(worker,j)]==count,(R,case['name'],'duplicate rank write',j)
    for path in root.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
    return {'kernel_ast_cases':len(cases)*2,'batch_sizes':[128,256],
        'verified':['exact key/id output','every batch cumulative left/right consumption','bounds','exactly one merge write per valid output slot'],
        'scope':'CPU execution of actual kernel AST; not device compilation or timing'}


if __name__=='__main__':print(json.dumps(validate(),indent=2))

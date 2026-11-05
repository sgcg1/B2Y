"""CPU execution of actual kernel bodies, without importing TileLang."""
import ast
import contextlib
import json
from pathlib import Path
from types import SimpleNamespace
import struct
from cases import build_cases,N,K,signed


class Tensor:
    def __init__(self,rows,track=False):self.rows=rows;self.writes={} if track else None
    def __getitem__(self,i):
        assert 0<=i<len(self.rows),i
        return self.rows[i]
    def __setitem__(self,i,v):
        assert 0<=i<len(self.rows),i
        self.rows[i]=v
        if self.writes is not None:self.writes[i]=self.writes.get(i,0)+1


def reinterpret(v,dtype):
    if dtype=='uint32':return struct.unpack('<I',struct.pack('<f',v))[0] if isinstance(v,float) else v&0xffffffff
    return signed(v&0xffffffff)


def validate():
    root=Path(__file__).resolve().parent;tree=ast.parse((root/'kernels.py').read_text(encoding='utf-8'))
    lang=SimpleNamespace(Kernel=lambda *a:contextlib.nullcontext(),SimtVF=lambda **k:contextlib.nullcontext(),
        alloc_shared=lambda shape,dtype:[0]*shape[0],alloc_var=lambda dtype:0,Parallel=range,serial=range,
        float32='float32',int32='int32',uint32='uint32',min=min,max=max,reinterpret=reinterpret,
        Cast=lambda dtype,v:v&0xffffffff if dtype=='uint32' else v,if_then_else=lambda c,a,b:a if c else b,
        copy=lambda src,dst:dst.__setitem__(slice(None),src.rows))
    count=0
    for name in ['encode_keys','collect_given_threshold']:
        outer=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
        encode=next(x for x in outer.body if isinstance(x,ast.FunctionDef) and x.name=='encode')
        main=next(x for x in outer.body if isinstance(x,ast.FunctionDef) and x.name=='main')
        code=compile(ast.fix_missing_locations(ast.Module(body=[encode]+main.body,type_ignores=[])),name,'exec')
        for case in build_cases():
            output=Tensor([-1]*(N if name=='encode_keys' else K),True);meta=Tensor([-1]*3)
            env={'T':lang,'N':N,'K':K,'G':128,'W':128,'x':Tensor(case['values']),
                 'starts':Tensor([case['start']]),'ends':Tensor([case['end']]),'threshold':Tensor([signed(case['threshold'])]),'out':output,'meta':meta}
            exec(code,env)
            if name=='encode_keys':assert output.rows==case['keys'],case['name']
            else:
                assert output.rows==case['ids'] and meta.rows==case['meta'],case['name']
                valid=min(K,case['end']-case['start'])
                assert all(output.writes[i]==(2 if i<valid else 1) for i in range(K))
            count+=1
    for path in root.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
    return {'actual_kernel_ast_cases':count,'inputs':24,'scope':'CPU logical validation only; no device performance',
            'verified':['complete canonical keys','exact threshold-given collection','stable tie','short-window padding','bounds and unique output writes']}


if __name__=='__main__':print(json.dumps(validate(),indent=2))

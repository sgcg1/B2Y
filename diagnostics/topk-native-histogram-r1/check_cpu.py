"""Compare whole-stream oracle with independent per-vector histogram accumulation."""
import ast
from pathlib import Path
import json
from cases import build_cases,expected,N

VARIANTS=[('full_zero',False,0,0),('masked_zero',True,0,0),('masked_seeded',True,7,11)]


def validate():
    count=0
    for name,masked,sf,sc in VARIANTS:
        for case in build_cases():
            got=[[sf]*128,[sf]*128,[sc]*128,[sc]*128]
            for offset in range(0,N,256):
                local=[0]*256
                for j in range(256):
                    if not masked or case['tags'][offset+j]!=0:local[case['digits'][offset+j]]+=1
                running=0
                for bucket in range(256):
                    running+=local[bucket]
                    bank=bucket//128;lane=bucket%128
                    got[bank][lane]+=local[bucket]
                    got[bank+2][lane]+=running
            assert got==expected(case,masked,sf,sc),(name,case['name'])
            count+=1
    for p in Path(__file__).parent.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
    return {'oracle_cases':count,'input_cases':len(build_cases()),'vectors_per_call':64,
            'variants':[v[0] for v in VARIANTS],
            'scope':'CPU oracle and per-vector mathematical model only; does not emulate native instruction or prove device semantics'}


if __name__=='__main__':print(json.dumps(validate(),indent=2))

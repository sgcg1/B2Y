"""Full N/K fixtures, CPU-supplied threshold and independent numerical selection oracle."""
import math
import random
import struct
N,K=16384,2048


def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]


def key(v):
    bits=struct.unpack('<I',struct.pack('<f',v))[0]
    magnitude=bits&0x7fffffff
    if magnitude>0x7f800000:return 0xffffffff
    if magnitude==0:return 0x80000000
    return (bits^0xffffffff) if bits>>31 else (bits^0x80000000)


def signed(v):return v if v<(1<<31) else v-(1<<32)


def expected(values,start,end):
    valid=list(range(start,end))
    def rank(i):return (1,0,-i) if math.isnan(values[i]) else (0,values[i],-i)
    winners=sorted(valid,key=rank,reverse=True)[:K]
    pivot=key(values[winners[-1]]) if len(valid)>K else 0
    above=[i for i in valid if key(values[i])>pivot]
    equal=[i for i in valid if key(values[i])==pivot]
    q=min(len(equal),max(0,K-len(above)))
    output=above+equal[:q]+[N]*(K-len(above)-q)
    assert sorted(i for i in output if i<N)==sorted(winners)
    return pivot,output,[len(above),len(equal),q]


def build_cases():
    rng=random.Random(20261105)
    normal=[f32(rng.gauss(0,1)) for _ in range(N)]
    specials=[float('nan'),float('inf'),-float('inf'),0.0,-0.0,f32(1e-40),f32(-1e-40)]
    arrays=[('random',normal),('equal',[1.0]*N),('quantized',[float(i%4) for i in range(N)]),
        ('close',[f32(1+i/(1<<23)) for i in range(N)]),
        ('special',[specials[i%len(specials)] for i in range(N)]),
        ('negative',[-float(i) for i in range(N)])]
    specs=[(name,values,0,N) for name,values in arrays]
    for width in [0,1,2047,2048,2049,4096,8192]:
        start=4093 if width<=4096 else 17
        specs.append(('window-'+str(width),normal,start,start+width))
    for i in range(11):
        values=[f32(rng.choice([rng.random(),1.0,0.0,-0.0,-1.0])) for _ in range(N)]
        start=rng.randrange(N+1);end=rng.randrange(start,N+1)
        specs.append(('mixed-'+str(i),values,start,end))
    rows=[]
    for name,values,start,end in specs:
        pivot,ids,meta=expected(values,start,end)
        rows.append({'name':name,'values':values,'start':start,'end':end,'threshold':pivot,'ids':ids,'meta':meta,'keys':[signed(key(v)) for v in values]})
    assert len(rows)==24
    return rows

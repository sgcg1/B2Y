"""Independent source-tagged full-sort oracle for exact multi-batch merging."""
import random
L,K,N = 2048,2048,16384


def build_cases():
    rng=random.Random(20261105)
    specs=[("interleaved",L,L,K,"interleaved"),("all-left",L,L,K,"left"),
           ("all-right",L,L,K,"right"),("ties-mixed-ids",L,L,K,"ties"),
           ("empty",0,0,K,"random"),("left-empty",0,L,K,"random"),
           ("right-empty",L,0,K,"random"),("short-tail",97,131,K,"extreme")]
    for limit in [0,1,127,128,129,255,256,257,511,512,513,2047,2048]:
        specs.append(("limit-"+str(limit),L,L,limit,"extreme"))
    for i in range(11):
        specs.append(("random-"+str(i),rng.randrange(L+1),rng.randrange(L+1),rng.randrange(K+1),rng.choice(["random","ties","extreme"])))
    result=[]
    for name,na,nb,limit,kind in specs:
        identifiers=rng.sample(range(N),na+nb)
        def key(side,i):
            if kind=="interleaved":return 0x80000000+2*(L-i)-side
            if kind=="left":return 0xffffffff if side==0 else 0
            if kind=="right":return 0 if side==0 else 0xffffffff
            if kind=="ties":return 0x80000000
            if kind=="extreme":return rng.choice([0,1,0x7fffffff,0x80000000,0xfffffffe,0xffffffff])
            return rng.randrange(1<<32)
        left=sorted([(key(0,i),idx) for i,idx in enumerate(identifiers[:na])],key=lambda x:(-x[0],x[1]))
        right=sorted([(key(1,i),idx) for i,idx in enumerate(identifiers[na:])],key=lambda x:(-x[0],x[1]))
        # No binary search, rank merge, or batched progression in this oracle.
        full=sorted([(k,i,0) for k,i in left]+[(k,i,1) for k,i in right],key=lambda x:(-x[0],x[1]))[:limit]
        result.append({"name":name,"left":left,"right":right,"limit":limit,"oracle":full})
    assert len(result)==32
    return result


def expected(case,R):
    full=case["oracle"]
    keys=[x[0] for x in full]+[0]*(K-len(full))
    ids=[x[1] for x in full]+[N]*(K-len(full))
    trace=[]
    for batch in range(K//R):
        prefix=full[:min((batch+1)*R,len(full))]
        a=sum(x[2]==0 for x in prefix)
        trace.append([a,len(prefix)-a,len(prefix)])
    return keys,ids,trace


def signed(key):
    return key if key < (1<<31) else key-(1<<32)

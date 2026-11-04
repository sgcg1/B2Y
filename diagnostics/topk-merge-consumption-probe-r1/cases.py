"""Deterministic inputs and independent full-merge consumption oracle."""
import random
R = 256


def build_cases():
    rng = random.Random(20261104)
    specs = [("empty",0,0,0,"equal"), ("left-empty",0,256,256,"equal"),
             ("right-empty",256,0,256,"equal"), ("all-from-left",256,256,256,"left"),
             ("all-from-right",256,256,256,"right"), ("zero-emitted",256,256,0,"random"),
             ("all-ties",256,256,256,"equal"), ("short-tail",7,9,16,"random"),
             ("one",1,1,1,"equal"), ("uint32-extremes",256,256,255,"extreme")]
    for i in range(86):
        a,b=rng.randrange(257),rng.randrange(257)
        specs.append(("random-"+str(i),a,b,rng.randrange(min(R,a+b)+1),rng.choice(["random","equal","extreme"])))
    result=[]
    for name,na,nb,m,kind in specs:
        ids=rng.sample(range(16384),na+nb)
        def key(side):
            if kind=="equal":return 0x80000000
            if kind=="left":return 0xffffffff if side==0 else 0
            if kind=="right":return 0 if side==0 else 0xffffffff
            if kind=="extreme":return rng.choice([0,1,0x7fffffff,0x80000000,0xfffffffe,0xffffffff])
            return rng.randrange(1<<32)
        left=sorted([(key(0),idx) for idx in ids[:na]],key=lambda p:(-p[0],p[1]))
        right=sorted([(key(1),idx) for idx in ids[na:]],key=lambda p:(-p[0],p[1]))
        # Source-tagged full sorting, not binary search or a reduction algorithm.
        merged=sorted([(k,i,1) for k,i in left]+[(k,i,0) for k,i in right],key=lambda p:(-p[0],p[1]))[:m]
        count_left=sum(item[2] for item in merged)
        last=merged[-1][:2] if merged else (0,0)
        result.append({"name":name,"left":left,"right":right,"m":m,"last":last,
                       "tags":[item[2] for item in merged],"expected":[count_left,m-count_left]})
    return result


def cpu_binary(case):
    lo,hi=0,len(case["left"])
    if case["m"]==0:return [0,0]
    z,zi=case["last"]
    for _ in range(9):
        if lo<hi:
            mid=(lo+hi)//2;k,i=case["left"][mid]
            if k>z or (k==z and i<=zi):lo=mid+1
            else:hi=mid
    assert lo==hi
    return [lo,case["m"]-lo]


def cpu_tree(case):
    values=case["tags"]+[0]*(R-case["m"])
    for level in range(8):
        stride=128>>level
        for i in range(stride):values[i]+=values[i+stride]
    return [values[0],case["m"]-values[0]]


if __name__=="__main__":
    import ast
    from pathlib import Path
    cases=build_cases()
    for case in cases:assert cpu_binary(case)==cpu_tree(case)==case["expected"],case["name"]
    for path in Path(__file__).parent.glob("*.py"):ast.parse(path.read_text(encoding="utf-8"))
    print("CPU_ORACLE_CHECKS_PASSED",len(cases),"cases; syntax passed")

"""Independent CPU algorithm prototype, not an NPU implementation or timer."""
import math
import random
import struct

N, K, PARTS, TILE = 16384, 2048, 4, 32


def ordered_key(value):
    bits = struct.unpack("<I", struct.pack("<f", value))[0]
    magnitude = bits & 0x7fffffff
    if magnitude > 0x7f800000:
        return 0xffffffff
    if magnitude == 0:
        return 0x80000000
    return (~bits & 0xffffffff) if bits >> 31 else bits | 0x80000000


def merge_topk(left, right, limit=K):
    result, i, j = [], 0, 0
    while len(result) < limit and (i < len(left) or j < len(right)):
        if j == len(right) or (i < len(left) and
                (left[i][0] > right[j][0] or
                 (left[i][0] == right[j][0] and left[i][1] < right[j][1]))):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    return result


def merge_topk_batched(left, right, limit=K, width=256):
    result, i, j = [], 0, 0
    while len(result) < limit and (i < len(left) or j < len(right)):
        head_left, head_right = left[i:i+width], right[j:j+width]
        batch = merge_topk(head_left, head_right, min(width,limit-len(result)))
        left_ids = {pair[1] for pair in head_left}
        consumed_left = sum(pair[1] in left_ids for pair in batch)
        consumed_right = len(batch)-consumed_left
        assert consumed_left+consumed_right > 0
        i += consumed_left
        j += consumed_right
        result.extend(batch)
    return result


def merge_tree(runs):
    while len(runs) > 1:
        runs = [merge_topk_batched(runs[i], runs[i+1]) if i+1 < len(runs) else runs[i]
                for i in range(0, len(runs), 2)]
    return runs[0] if runs else []


def select(values, start=0, end=N):
    assert len(values) == N and 0 <= start <= end <= N
    local = []
    for part in range(PARTS):
        lo, hi = part * (N//PARTS), (part+1) * (N//PARTS)
        runs = []
        for tile in range(lo, hi, TILE):
            run = [(ordered_key(values[i]), i) for i in range(max(tile,start), min(tile+TILE,end))]
            runs.append(sorted(run, key=lambda pair: (-pair[0],pair[1])))
        local.append(merge_tree(runs))
    final = merge_tree(local)
    return [index for _,index in final] + [N] * (K-len(final))


def oracle(values, start, end):
    # Independent numeric ordering, without the bit-key transform or merge tree.
    def rank(i):
        value = values[i]
        return (1,0,-i) if math.isnan(value) else (0,value,-i)
    ids = sorted(range(start,end), key=rank, reverse=True)[:K]
    return ids+[N]*(K-len(ids))


def validate():
    rng = random.Random(20261104)
    random_values = [struct.unpack("<f",struct.pack("<f",rng.gauss(0,1)))[0] for _ in range(N)]
    cases = [("random",random_values,0,N), ("all-equal",[1.0]*N,0,N),
             ("four-level",[float(i%4) for i in range(N)],0,N),
             ("increasing",list(map(float,range(N))),0,N),
             ("decreasing",list(map(float,range(N-1,-1,-1))),0,N),
             ("all-winners-in-one-part",[100.0]*(N//4)+[0.0]*(N-N//4),0,N),
             ("nan-inf-zero",[float("nan"),float("inf"),-float("inf"),0.0,-0.0]*3276+[1.0]*4,0,N)]
    for count in [0,1,2047,2048,2049,4096,8192]:
        start=4093 if count<=4096 else 17
        cases.append(("window-"+str(count),random_values,start,start+count))
    for seed in range(16):
        values=[rng.choice([rng.random(),1.0,0.0,-0.0,-1.0]) for _ in range(N)]
        start=rng.randrange(N+1);end=rng.randrange(start,N+1)
        cases.append(("mixed-"+str(seed),values,start,end))
    rows=[]
    for name,values,start,end in cases:
        actual=select(values,start,end)
        assert actual==oracle(values,start,end),name
        valid=[i for i in actual if i<N]
        assert len(valid)==len(set(valid))==min(K,end-start),name
        rows.append({"name":name,"window":[start,end],"passed":True})
    # A concrete counterexample to keeping K/P items per partition.
    wrong=[list(range(part*(N//4),part*(N//4)+K//PARTS)) for part in range(PARTS)]
    true_set=set(range(K))
    assert len(true_set.intersection(i for run in wrong for i in run))==K//PARTS
    return {"implementation":"CPU reference only; no timing claims", "N":N,"K":K,"parts":PARTS,
            "cases":rows,"case_count":len(rows),"unsafe_local_K_over_P_counterexample":"Only 512 of 2048 true winners retained",
            "logical_full_window_GM_bytes":N*4+2*PARTS*K*8+K*4}


if __name__ == "__main__":
    import json
    print(json.dumps(validate(),indent=2))

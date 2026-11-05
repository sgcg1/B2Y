"""Independent scalar count/prefix oracle, fixed uint8 inputs and nonbinary tags."""
import random
N=16384


def build_cases():
    rng=random.Random(20261105)
    ramp=[i%256 for i in range(N)]
    one=[1]*N
    cases=[{'name':'ramp','digits':ramp,'tags':one}]
    for value in [0,127,128,255]:cases.append({'name':'constant-'+str(value),'digits':[value]*N,'tags':one})
    cases.append({'name':'random','digits':[rng.randrange(256) for _ in range(N)],'tags':one})
    for length in [0,1,127,128,129,255,256,257,N-1]:
        cases.append({'name':'prefix-'+str(length),'digits':ramp,'tags':[1 if i<length else 0 for i in range(N)]})
    cases.append({'name':'alternating-mask','digits':ramp,'tags':[i%2 for i in range(N)]})
    cases.append({'name':'random-nonbinary-mask','digits':[rng.randrange(256) for _ in range(N)],'tags':[rng.choice([0,1,2,255]) for _ in range(N)]})
    cases.append({'name':'vector-boundaries','digits':[127 if i%256==255 else 128 if i%256==0 else 255 for i in range(N)],'tags':one})
    return cases


def expected(case,masked,seed_f,seed_c):
    counts=[0]*256
    for value,tag in zip(case['digits'],case['tags']):
        if not masked or tag!=0:counts[value]+=1
    prefix=[];total=0
    for value in counts:total+=value;prefix.append(total)
    answer=[[v+seed_f for v in counts[:128]],[v+seed_f for v in counts[128:]],
            [v+seed_c for v in prefix[:128]],[v+seed_c for v in prefix[128:]]]
    assert max(max(row) for row in answer)<=65535
    return answer

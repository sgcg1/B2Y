"""Exact multi-batch rank merge. No library scan/reduce/merge/atomic dependence."""
import tilelang
import tilelang.ascend.language as T


@tilelang.jit(target="ascend", out_idx=[])
def merge_batches(B: int, R: int = 256):
    assert R in (128,256)
    L,K,STEPS = 2048,2048,R.bit_length()
    @T.prim_func
    def main(keys: T.Tensor((B,2,L),T.int32), ids: T.Tensor((B,2,L),T.int32),
             lengths: T.Tensor((B,2),T.int32), limits: T.Tensor((B,),T.int32),
             out_key: T.Tensor((B,K),T.int32), out_id: T.Tensor((B,K),T.int32),
             trace: T.Tensor((B,K//R,3),T.int32)):
        with T.Kernel(B) as case:
            head_key = T.alloc_shared((2*R,),T.int32)
            head_id = T.alloc_shared((2*R,),T.int32)
            left_rank = T.alloc_shared((R,),T.int32)
            state = T.alloc_shared((3,),T.int32)
            with T.SimtVF(threads=128):
                for i in T.Parallel(K):
                    out_key[case,i] = 0
                    out_id[case,i] = 16384
                for i in T.Parallel(3):
                    state[i] = 0
            for batch in T.serial(K//R):
                with T.SimtVF(threads=128):
                    for p in T.Parallel(2*R):
                        side = T.if_then_else(p < R,0,1)
                        j = p % R
                        if j < T.min(R,lengths[case,side]-state[side]):
                            head_key[p] = keys[case,side,state[side]+j]
                            head_id[p] = ids[case,side,state[side]+j]
                        else:
                            head_key[p] = 0
                            head_id[p] = 16384
                with T.SimtVF(threads=128):
                    for p in T.Parallel(2*R):
                        side = T.if_then_else(p < R,0,1)
                        j = p % R
                        own = T.min(R,lengths[case,side]-state[side])
                        other = T.min(R,lengths[case,1-side]-state[1-side])
                        take = T.min(R,T.min(limits[case]-state[2],lengths[case,0]+lengths[case,1]-state[2]))
                        if j < own and take > 0:
                            lo = T.alloc_var(T.int32)
                            hi = T.alloc_var(T.int32)
                            mid = T.alloc_var(T.int32)
                            lo = 0
                            hi = other
                            for step in T.serial(STEPS):
                                if lo < hi:
                                    mid = (lo+hi)//2
                                    their_key = T.reinterpret(head_key[(1-side)*R+mid],T.uint32)
                                    our_key = T.reinterpret(head_key[p],T.uint32)
                                    if their_key > our_key or (their_key == our_key and head_id[(1-side)*R+mid] < head_id[p]):
                                        lo = mid+1
                                    else:
                                        hi = mid
                            rank = j+lo
                            if side == 0:
                                left_rank[j] = rank
                            if rank < take:
                                out_key[case,state[2]+rank] = head_key[p]
                                out_id[case,state[2]+rank] = head_id[p]
                with T.SimtVF(threads=128):
                    for thread in T.Parallel(128):
                        if thread == 0:
                            take = T.min(R,T.min(limits[case]-state[2],lengths[case,0]+lengths[case,1]-state[2]))
                            lo = T.alloc_var(T.int32)
                            hi = T.alloc_var(T.int32)
                            mid = T.alloc_var(T.int32)
                            lo = 0
                            hi = T.min(R,lengths[case,0]-state[0])
                            if take > 0:
                                for step in T.serial(STEPS):
                                    if lo < hi:
                                        mid = (lo+hi)//2
                                        if left_rank[mid] < take:
                                            lo = mid+1
                                        else:
                                            hi = mid
                            else:
                                lo = 0
                            state[0] = state[0]+lo
                            state[1] = state[1]+take-lo
                            state[2] = state[2]+take
                            trace[case,batch,0] = state[0]
                            trace[case,batch,1] = state[1]
                            trace[case,batch,2] = state[2]
    return main

"""Independent scan versus aggregate consumption probes; not a merge/TopK kernel."""
import tilelang
import tilelang.ascend.language as T


@tilelang.jit(target="ascend", out_idx=[])
def consume_binary(B: int, R: int = 256):
    assert R == 256
    @T.prim_func
    def main(left_key: T.Tensor((B,R),T.int32), left_id: T.Tensor((B,R),T.int32),
             lengths: T.Tensor((B,),T.int32), emitted: T.Tensor((B,),T.int32),
             last_key: T.Tensor((B,),T.int32), last_id: T.Tensor((B,),T.int32),
             out: T.Tensor((B,2),T.int32)):
        with T.Kernel(B) as case:
            with T.SimtVF(threads=128):
                for thread in T.Parallel(128):
                    if thread == 0:
                        lo = T.alloc_var(T.int32)
                        hi = T.alloc_var(T.int32)
                        mid = T.alloc_var(T.int32)
                        lo = 0
                        hi = lengths[case]
                        if emitted[case] > 0:
                            for step in T.serial(9):
                                if lo < hi:
                                    mid = (lo+hi)//2
                                    key = T.reinterpret(left_key[case,mid],T.uint32)
                                    pivot = T.reinterpret(last_key[case],T.uint32)
                                    if key > pivot or (key == pivot and left_id[case,mid] <= last_id[case]):
                                        lo = mid+1
                                    else:
                                        hi = mid
                        else:
                            lo = 0
                        out[case,0] = lo
                        out[case,1] = emitted[case]-lo
    return main


@tilelang.jit(target="ascend", out_idx=[])
def consume_tree(B: int, R: int = 256):
    assert R == 256
    @T.prim_func
    def main(tags: T.Tensor((B,R),T.int32), emitted: T.Tensor((B,),T.int32),
             out: T.Tensor((B,2),T.int32)):
        with T.Kernel(B) as case:
            work = T.alloc_shared((R,),T.int32)
            scratch = T.alloc_shared((128,),T.int32)
            with T.SimtVF(threads=128):
                for i in T.Parallel(R):
                    work[i] = T.if_then_else(i < emitted[case],tags[case,i],0)
            # Double buffering separates reads and writes within each VF.
            # Two VF calls per level establish the inter-level dependency.
            for level in T.serial(8):
                with T.SimtVF(threads=128):
                    for i in T.Parallel(128):
                        if i < (128 >> level):
                            scratch[i] = work[i]+work[i+(128 >> level)]
                with T.SimtVF(threads=128):
                    for i in T.Parallel(128):
                        if i < (128 >> level):
                            work[i] = scratch[i]
            with T.SimtVF(threads=128):
                for i in T.Parallel(128):
                    if i == 0:
                        out[case,0] = work[0]
                        out[case,1] = emitted[case]-work[0]
    return main


@tilelang.jit(target="ascend", out_idx=[])
def scan_control(R: int = 256):
    @T.prim_func
    def main(x: T.Tensor((R,),T.int32), out: T.Tensor((R,),T.int32)):
        with T.Kernel(1):
            src = T.alloc_shared((R,),T.int32)
            dst = T.alloc_shared((R,),T.int32)
            with T.SimtVF(threads=128):
                for i in T.Parallel(R):
                    src[i] = x[i]
            T.cumsum(src,dst,dim=0)
            with T.SimtVF(threads=128):
                for i in T.Parallel(R):
                    out[i] = dst[i]
    return main

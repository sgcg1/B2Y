import tilelang
import tilelang.ascend.language as T


@tilelang.jit(target="ascend", out_idx=[])
def repro(N: int, BYTE: bool):
    @T.prim_func
    def main(x: T.Tensor((N,), T.int32), out: T.Tensor((N,), T.int32)):
        with T.Kernel(1):
            cache = T.alloc_shared((N,), T.uint8 if BYTE else T.uint32)
            hist = T.alloc_shared((256,), T.int32)
            with T.SimtVF(threads=128):
                for i in T.Parallel(256):
                    hist[i] = 0
            with T.SimtVF(threads=128):
                for tile in T.serial(T.ceildiv(N, 128)):
                    for lane in T.Parallel(128):
                        i = tile * 128 + lane
                        digit = T.max(0, T.min(x[i], 255))
                        cache[i] = T.Cast(T.uint8 if BYTE else T.uint32, digit)
                        if digit > 0:
                            T.atomic_add(hist[digit], 1)
            with T.SimtVF(threads=128):
                for tile in T.serial(T.ceildiv(N, 128)):
                    for lane in T.Parallel(128):
                        i = tile * 128 + lane
                        out[i] = T.Cast(T.int32, cache[i]) + hist[i % 256]
    return main

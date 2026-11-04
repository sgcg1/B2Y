"""Solution-A P0 capability probe kernels: histogram lowering, not a TopK implementation.

Goal: determine on the server's TileLang build whether a 256-bin histogram can be
expressed WITHOUT per-element atomic scatter, and whether a vector-histogram / scan /
sort primitive is exposed. Each function is self-contained and returns a prim_func.

Candidates:
  * hist_atomic_scatter  — control replicating the current slow path (per-element atomic_add).
  * hist_bucket_reduce   — Solution-A target (per-bucket masked reduction, no scatter atomic).
"""

import tilelang
import tilelang.ascend.language as T


def _coarse_byte(value):
    # FP16 monotonic-order top byte; reuses the exact transform from the retained kernels.
    bits = T.reinterpret(T.Cast(T.float16, value), T.uint16)
    magnitude = bits & T.Cast(T.uint16, 32767)
    ordered = T.if_then_else(
        bits & T.Cast(T.uint16, 32768) != 0, ~bits, bits | T.Cast(T.uint16, 32768)
    )
    zeroed = T.if_then_else(magnitude == 0, T.Cast(T.uint16, 32768), ordered)
    canonical = T.if_then_else(
        magnitude > T.Cast(T.uint16, 31744), T.Cast(T.uint16, 65535), zeroed
    )
    return T.Cast(T.int32, canonical >> 8 & T.Cast(T.uint16, 255))


@tilelang.jit(target="ascend", out_idx=[])
def hist_atomic_scatter(N: int):
    """Control: histogram via per-element atomic_add on a shared 256-bin buffer."""

    @T.prim_func
    def main(x: T.Tensor((N,), T.float32), out: T.Tensor((256,), T.int32)):
        with T.Kernel(1):
            hist = T.alloc_shared((256,), T.int32)
            with T.SimtVF(threads=128):
                for bucket in T.Parallel(256):
                    hist[bucket] = 0
            with T.SimtVF(threads=128):
                for tile in T.serial(T.ceildiv(N, 128)):
                    for lane in T.Parallel(128):
                        i = tile * 128 + lane
                        if i < N:
                            digit = T.alloc_var(T.int32)
                            digit = _coarse_byte(x[i])
                            T.atomic_add(hist[T.max(0, T.min(digit, 255))], 1)
            with T.SimtVF(threads=128):
                for bucket in T.Parallel(256):
                    out[bucket] = hist[bucket]

    return main


@tilelang.jit(target="ascend", out_idx=[])
def hist_bucket_reduce(N: int):
    """Solution-A target: histogram via a per-bucket masked reduction, no scatter atomic.

    For each of 256 buckets, count the digits equal to that bucket. This is O(256*N)
    but lowers to vector compare+accumulate if TileLang emits it atomic-free.
    """

    @T.prim_func
    def main(x: T.Tensor((N,), T.float32), out: T.Tensor((256,), T.int32)):
        with T.Kernel(1):
            digits = T.alloc_shared((N,), T.int32)
            hist = T.alloc_shared((256,), T.int32)
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):
                    digits[i] = _coarse_byte(x[i])
            with T.SimtVF(threads=128):
                for bucket in T.Parallel(256):
                    acc = T.alloc_var(T.int32)
                    acc = 0
                    for j in T.serial(N):
                        acc = acc + T.if_then_else(digits[j] == bucket, 1, 0)
                    hist[bucket] = acc
            with T.SimtVF(threads=128):
                for bucket in T.Parallel(256):
                    out[bucket] = hist[bucket]

    return main
"""Solution-A follow-up capability probe kernels: scan (prefix-sum) and reduce lowering.

Goal: determine on the server's TileLang build whether the vector primitives that
``probe-summary.txt`` surfaced — ``cumsum`` and the ``reduce_sum`` / ``vreduce_sum``
family — actually lower to vector/SIMD instructions, or fall back to scalar serial
loops. This decides whether the ``finish`` / ``compact`` kernels can be rewritten as
"vector prefix-sum + multi-core" instead of per-element atomic scatter + thread-0
serial prefix.

Candidates (each self-contained, returns a prim_func):
  * cumsum_ub_probe        — T.cumsum on a shared 1-D buffer (the target rewrite path).
  * reduce_sum_ub_probe    — T.reduce_sum on a shared 2-D buffer (buffer-level API).
  * vreduce_sum_simd_probe — T.vreduce_sum on fragments in T.SimdVF (positive control,
                             already used in local FA kernels, lowers to npu.reduce).
  * serial_prefix_ctrl     — thread-0 serial prefix (negative control, replicates the
                             current finish kernel's serial-prefix pattern).
"""

import tilelang
import tilelang.ascend.language as T


@tilelang.jit(target="ascend", out_idx=[])
def cumsum_ub_probe(N: int):
    """T.cumsum on a 1-D shared buffer. The key unknown: vector scan vs serial loop."""

    @T.prim_func
    def main(x: T.Tensor((N,), T.int32), out: T.Tensor((N,), T.int32)):
        with T.Kernel(1):
            src = T.alloc_shared((N,), T.int32)
            dst = T.alloc_shared((N,), T.int32)
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):
                    src[i] = x[i]
            T.cumsum(src, dst, dim=0)
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):
                    out[i] = dst[i]

    return main


@tilelang.jit(target="ascend", out_idx=[])
def reduce_sum_ub_probe(R: int, C: int):
    """T.reduce_sum on a shared [R, C] buffer along dim=1 (buffer-level API)."""

    @T.prim_func
    def main(x: T.Tensor((R, C), T.int32), out: T.Tensor((R,), T.int32)):
        with T.Kernel(1):
            src = T.alloc_shared((R, C), T.int32)
            dst = T.alloc_shared((R,), T.int32)
            with T.SimtVF(threads=128):
                for i in T.Parallel(R * C):
                    src[i // C, i % C] = x[i // C, i % C]
            T.reduce_sum(src, dst, dim=1, clear=True)
            with T.SimtVF(threads=128):
                for i in T.Parallel(R):
                    out[i] = dst[i]

    return main


@tilelang.jit(target="ascend", out_idx=[])
def vreduce_sum_simd_probe(R: int, C: int):
    """T.vreduce_sum on fragments in T.SimdVF — positive control for vector reduce."""

    @T.prim_func
    def main(x: T.Tensor((R, C), T.int32), out: T.Tensor((R,), T.int32)):
        with T.Kernel(1):
            src = T.alloc_shared((R, C), T.int32)
            dst = T.alloc_shared((R,), T.int32)
            with T.SimtVF(threads=128):
                for i in T.Parallel(R * C):
                    src[i // C, i % C] = x[i // C, i % C]
            with T.SimdVF():
                frag = T.alloc_frag((R, C), T.int32)
                out_frag = T.alloc_frag((R,), T.int32)
                T.copy(src, frag)
                T.vreduce_sum(frag, out_frag, dim=1)
                T.copy(out_frag, dst)
            with T.SimtVF(threads=128):
                for i in T.Parallel(R):
                    out[i] = dst[i]

    return main


@tilelang.jit(target="ascend", out_idx=[])
def serial_prefix_ctrl(N: int):
    """Negative control: thread-0-only serial inclusive prefix (finish's current form)."""

    @T.prim_func
    def main(x: T.Tensor((N,), T.int32), out: T.Tensor((N,), T.int32)):
        with T.Kernel(1):
            src = T.alloc_shared((N,), T.int32)
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):
                    src[i] = x[i]
                for thread in T.Parallel(128):
                    if thread == 0:
                        total = T.alloc_var(T.int32)
                        total = 0
                        for i in T.serial(N):
                            total = total + src[i]
                            src[i] = total
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):
                    out[i] = src[i]

    return main
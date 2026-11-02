"""Minimal mainline Ascend VF workload; not a production TopK implementation."""

import tilelang
import tilelang.ascend.language as T

PRELUDE = r"""
#include "kernel_operator.h"
__aicore__ inline int32_t tileops_probe_fence() {
    AscendC::PipeBarrier<PIPE_ALL>();
    return 0;
}
__aicore__ inline int64_t tileops_probe_clock() {
    return AscendC::GetSystemCycle();
}
"""


@tilelang.jit(target="ascend", out_idx=[])
def timer_probe(N: int, REPEATS: int, MODE: int):
    # MODE: 0=plain, 1=fences, 2=fences+counter. The counter domain is not AICore MHz.
    assert MODE in (0, 1, 2) and REPEATS >= 0
    prelude = PRELUDE if MODE else ""

    @T.prim_func
    def main(
        x: T.Tensor((N,), T.float32),
        y: T.Tensor((N,), T.float32),
        ticks: T.Tensor((2,), T.int64),
    ):
        with T.Kernel(1, prelude=prelude):
            values = T.alloc_shared((N,), T.float32)
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):
                    values[i] = x[i]
            if MODE > 0:
                T.evaluate(T.call_extern("int32", "tileops_probe_fence"))
            if MODE == 2:
                ticks[0] = T.call_extern("int64", "tileops_probe_clock")
            if REPEATS > 0:
                for _repeat in T.serial(REPEATS):
                    with T.SimtVF(threads=128):
                        for i in T.Parallel(N):
                            values[i] = values[i] + 1.0
            if MODE > 0:
                T.evaluate(T.call_extern("int32", "tileops_probe_fence"))
            if MODE == 2:
                ticks[1] = T.call_extern("int64", "tileops_probe_clock")
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):
                    y[i] = values[i]

    return main

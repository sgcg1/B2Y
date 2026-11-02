"""Minimal mainline Ascend VF workload; not a production TopK implementation."""

import tilelang
import tilelang.ascend.language as T

PRELUDE = r"""
#include "kernel_operator.h"
__aicore__ inline int32_t tileops_probe2_keep_ticks(__gm__ int64_t* ticks) {
    return 0;
}
"""


@tilelang.jit(target="ascend", out_idx=[])
def timer_probe(N: int, REPEATS: int, MODE: int):
    # MODE changes a source/IR fingerprint; instrumentation is added AFTER scheduling.
    assert MODE in (0, 1, 2) and REPEATS >= 0
    prelude = f"// TILEOPS_TIMER_PROBE2 mode={MODE} repeats={REPEATS}\n" + PRELUDE

    @T.prim_func
    def main(
        x: T.Tensor((N,), T.float32),
        y: T.Tensor((N,), T.float32),
        ticks: T.Tensor((2,), T.int64),
    ):
        with T.Kernel(1, prelude=prelude):
            values = T.alloc_shared((N,), T.float32)
            # Retain the clock-buffer ABI, then remove this no-op in postprocessing.
            T.evaluate(T.call_extern("int32", "tileops_probe2_keep_ticks", T.address_of(ticks[0])))
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):
                    values[i] = x[i]
            if REPEATS > 0:
                for _repeat in T.serial(REPEATS):
                    with T.SimtVF(threads=128):
                        for i in T.Parallel(N):
                            values[i] = values[i] + 1.0
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):
                    y[i] = values[i]

    return main

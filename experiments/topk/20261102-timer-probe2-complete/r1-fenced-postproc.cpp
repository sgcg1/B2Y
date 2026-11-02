#include <tl_templates/ascend/common.h>
#include <tl_templates/ascend/debug.h>
// TILEOPS_TIMER_PROBE2 mode=1 repeats=1

#include "kernel_operator.h"
__aicore__ inline int32_t tileops_probe2_keep_ticks(__gm__ int64_t* ticks) {
    return 0;
}


__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_0(__ubuf__ float* values, __gm__ float* x) {
  #pragma unroll
  for (int32_t i = 0; i < 16; ++i) {
    *(__ubuf__ float2*)(values + ((i * 256) + (((int32_t)threadIdx.x) * 2))) = *(__gm__ float2*)(x + ((i * 256) + (((int32_t)threadIdx.x) * 2)));
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_1(__ubuf__ float* values) {
  #pragma unroll
  for (int32_t i = 0; i < 16; ++i) {
    float broadcast_var = float(0x1p+0f/*1.000000e+00*/);
    *(__ubuf__ float2*)(values + ((i * 256) + (((int32_t)threadIdx.x) * 2))) = (*(__ubuf__ float2*)(values + ((i * 256) + (((int32_t)threadIdx.x) * 2))) + make_float2(broadcast_var, broadcast_var));
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_2(__gm__ float* y, __ubuf__ float* values) {
  #pragma unroll
  for (int32_t i = 0; i < 16; ++i) {
    *(__gm__ float2*)(y + ((i * 256) + (((int32_t)threadIdx.x) * 2))) = *(__ubuf__ float2*)(values + ((i * 256) + (((int32_t)threadIdx.x) * 2)));
  }
}


#include <tl_templates/ascend/dcache_bypass.h>
__aicore__ inline void tileops_probe2_begin(__gm__ int64_t* ticks) {
    AscendC::PipeBarrier<PIPE_ALL>();
    
}
__aicore__ inline void tileops_probe2_end(__gm__ int64_t* ticks) {
    AscendC::PipeBarrier<PIPE_ALL>();
    
}
extern "C" __global__ __vector__ void main_kernel(__gm__ int64_t* ticks, __gm__ float* x, __gm__ float* y) {
  asc_init();
  __ubuf__ float *values = (__ubuf__ float *)0;

  asc_vf_call<main_kernel_simt_vf_0>(cce::dim3(128), values, x);
  tileops_probe2_begin(ticks);
  asc_vf_call<main_kernel_simt_vf_1>(cce::dim3(128), values);

  tileops_probe2_end(ticks);
  asc_vf_call<main_kernel_simt_vf_2>(cce::dim3(128), y, values);
}


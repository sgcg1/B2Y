#include <tl_templates/ascend/common.h>
#include <tl_templates/ascend/debug.h>
__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_0(__ubuf__ int32_t* src, __gm__ int32_t* x) {
  int32_t total = 0;
  #pragma unroll
  for (int32_t i = 0; i < 16; ++i) {
    *(__ubuf__ int2*)(src + ((i * 256) + (((int32_t)threadIdx.x) * 2))) = *(__gm__ int2*)(x + ((i * 256) + (((int32_t)threadIdx.x) * 2)));
  }
  asc_syncthreads();
  if (((int32_t)threadIdx.x) == 0) {
    total = 0;
    for (int32_t i_1 = 0; i_1 < 4096; ++i_1) {
      total = (total + src[i_1]);
      src[i_1] = total;
    }
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_1(__gm__ int32_t* out, __ubuf__ int32_t* src) {
  #pragma unroll
  for (int32_t i = 0; i < 16; ++i) {
    *(__gm__ int2*)(out + ((i * 256) + (((int32_t)threadIdx.x) * 2))) = *(__ubuf__ int2*)(src + ((i * 256) + (((int32_t)threadIdx.x) * 2)));
  }
}

extern "C" __global__ __vector__ void main_kernel(__gm__ int32_t* out, __gm__ int32_t* x) {
  asc_init();
  __ubuf__ int32_t *src = (__ubuf__ int32_t *)0;
  asc_vf_call<main_kernel_simt_vf_0>(cce::dim3(128), src, x);
  asc_vf_call<main_kernel_simt_vf_1>(cce::dim3(128), out, src);
}


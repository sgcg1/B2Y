#include <tl_templates/ascend/common.h>
#include <tl_templates/ascend/debug.h>
__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_0(__ubuf__ uint8_t* buf_dyn_shmem) {
  int32_t broadcast_var = 0;
  *(__ubuf__ int2*)(((__ubuf__ int32_t*)buf_dyn_shmem) + ((((int32_t)threadIdx.x) * 2) + 4096)) = make_int2(broadcast_var, broadcast_var);
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_1(__gm__ int32_t* x, __ubuf__ uint8_t* buf_dyn_shmem) {
  for (int32_t tile = 0; tile < 128; ++tile) {
    int32_t digit = max(0, min(x[((tile * 128) + ((int32_t)threadIdx.x))], 255));
    asc_syncthreads();
    buf_dyn_shmem[((tile * 128) + ((int32_t)threadIdx.x))] = ((uint8_t)digit);
    asc_syncthreads();
    if (0 < digit) {
      asc_atomic_add((&(((__ubuf__ int32_t*)buf_dyn_shmem)[(((int64_t)digit) + (int64_t)4096)])), 1);
    }
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_2(__gm__ int32_t* out, __ubuf__ uint8_t* buf_dyn_shmem) {
  for (int32_t tile = 0; tile < 128; ++tile) {
    out[((tile * 128) + ((int32_t)threadIdx.x))] = (((int32_t)buf_dyn_shmem[((tile * 128) + ((int32_t)threadIdx.x))]) + ((__ubuf__ int32_t*)buf_dyn_shmem)[((((tile & 1) * 128) + ((int32_t)threadIdx.x)) + 4096)]);
  }
}

extern "C" __global__ __vector__ void main_kernel(__gm__ int32_t* out, __gm__ int32_t* x) {
  asc_init();
  __ubuf__ uint8_t *buf_dyn_shmem = (__ubuf__ uint8_t *)0;
  asc_vf_call<main_kernel_simt_vf_0>(cce::dim3(128), buf_dyn_shmem);
  asc_vf_call<main_kernel_simt_vf_1>(cce::dim3(128), x, buf_dyn_shmem);
  asc_vf_call<main_kernel_simt_vf_2>(cce::dim3(128), out, buf_dyn_shmem);
}


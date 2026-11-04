#include <tl_templates/ascend/common.h>
#include <tl_templates/ascend/debug.h>
__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_0(__ubuf__ uint8_t* buf_dyn_shmem, __gm__ float* x) {
  #pragma unroll
  for (int32_t i = 0; i < 128; ++i) {
      half v_ = (half)x[((i * 128) + ((int32_t)threadIdx.x))];
    uint16_t condval;
    if (((uint16_t)31744 < ((*(uint16_t *)(&(v_))) & (uint16_t)32767))) {
      condval = (uint16_t)65535;
    } else {
        half v__1 = (half)x[((i * 128) + ((int32_t)threadIdx.x))];
      uint16_t condval_1;
      if ((((int32_t)((*(uint16_t *)(&(v__1))) & (uint16_t)32767)) == 0)) {
        condval_1 = (uint16_t)32768;
      } else {
          half v__2 = (half)x[((i * 128) + ((int32_t)threadIdx.x))];
        uint16_t condval_2;
        if ((0 < ((int32_t)((*(uint16_t *)(&(v__2))) & (uint16_t)32768)))) {
            half v__3 = (half)x[((i * 128) + ((int32_t)threadIdx.x))];
          condval_2 = (~(*(uint16_t *)(&(v__3))));
        } else {
            half v__4 = (half)x[((i * 128) + ((int32_t)threadIdx.x))];
          condval_2 = ((*(uint16_t *)(&(v__4))) | (uint16_t)32768);
        }
        condval_1 = condval_2;
      }
      condval = condval_1;
    }
    ((__ubuf__ int32_t*)buf_dyn_shmem)[((i * 128) + ((int32_t)threadIdx.x))] = ((int32_t)((condval >> (uint16_t)8) & (uint16_t)255));
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_1(__ubuf__ uint8_t* buf_dyn_shmem) {
  int32_t acc = 0;
  #pragma unroll
  for (int32_t i = 0; i < 2; ++i) {
    acc = 0;
    for (int32_t j = 0; j < 16384; ++j) {
      int32_t condval;
      if ((((__ubuf__ int32_t*)buf_dyn_shmem)[j] == ((i * 128) + ((int32_t)threadIdx.x)))) {
        condval = 1;
      } else {
        condval = 0;
      }
      acc = (acc + condval);
    }
    ((__ubuf__ int32_t*)buf_dyn_shmem)[(((i * 128) + ((int32_t)threadIdx.x)) + 16384)] = acc;
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_2(__gm__ int32_t* out, __ubuf__ uint8_t* buf_dyn_shmem) {
  *(__gm__ int2*)(out + (((int32_t)threadIdx.x) * 2)) = *(__ubuf__ int2*)(((__ubuf__ int32_t*)buf_dyn_shmem) + ((((int32_t)threadIdx.x) * 2) + 16384));
}

extern "C" __global__ __vector__ void main_kernel(__gm__ int32_t* out, __gm__ float* x) {
  asc_init();
  __ubuf__ uint8_t *buf_dyn_shmem = (__ubuf__ uint8_t *)0;
  asc_vf_call<main_kernel_simt_vf_0>(cce::dim3(128), buf_dyn_shmem, x);
  asc_vf_call<main_kernel_simt_vf_1>(cce::dim3(128), buf_dyn_shmem);
  asc_vf_call<main_kernel_simt_vf_2>(cce::dim3(128), out, buf_dyn_shmem);
}


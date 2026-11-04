#include <tl_templates/ascend/common.h>
#include <tl_templates/ascend/debug.h>
__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_0(__ubuf__ int32_t* hist) {
  int32_t broadcast_var = 0;
  *(__ubuf__ int2*)(hist + (((int32_t)threadIdx.x) * 2)) = make_int2(broadcast_var, broadcast_var);
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_1(__gm__ float* x, __ubuf__ int32_t* hist) {
  int32_t digit = 0;
  for (int32_t tile = 0; tile < 128; ++tile) {
      half v_ = (half)x[((tile * 128) + ((int32_t)threadIdx.x))];
    uint16_t condval;
    if (((uint16_t)31744 < ((*(uint16_t *)(&(v_))) & (uint16_t)32767))) {
      condval = (uint16_t)65535;
    } else {
        half v__1 = (half)x[((tile * 128) + ((int32_t)threadIdx.x))];
      uint16_t condval_1;
      if ((((int32_t)((*(uint16_t *)(&(v__1))) & (uint16_t)32767)) == 0)) {
        condval_1 = (uint16_t)32768;
      } else {
          half v__2 = (half)x[((tile * 128) + ((int32_t)threadIdx.x))];
        uint16_t condval_2;
        if ((0 < ((int32_t)((*(uint16_t *)(&(v__2))) & (uint16_t)32768)))) {
            half v__3 = (half)x[((tile * 128) + ((int32_t)threadIdx.x))];
          condval_2 = (~(*(uint16_t *)(&(v__3))));
        } else {
            half v__4 = (half)x[((tile * 128) + ((int32_t)threadIdx.x))];
          condval_2 = ((*(uint16_t *)(&(v__4))) | (uint16_t)32768);
        }
        condval_1 = condval_2;
      }
      condval = condval_1;
    }
    digit = ((int32_t)((condval >> (uint16_t)8) & (uint16_t)255));
    asc_atomic_add((&(hist[max(0, min(digit, 255))])), 1);
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_2(__gm__ int32_t* out, __ubuf__ int32_t* hist) {
  *(__gm__ int2*)(out + (((int32_t)threadIdx.x) * 2)) = *(__ubuf__ int2*)(hist + (((int32_t)threadIdx.x) * 2));
}

extern "C" __global__ __vector__ void main_kernel(__gm__ int32_t* out, __gm__ float* x) {
  asc_init();
  __ubuf__ int32_t *hist = (__ubuf__ int32_t *)0;
  asc_vf_call<main_kernel_simt_vf_0>(cce::dim3(128), hist);
  asc_vf_call<main_kernel_simt_vf_1>(cce::dim3(128), x, hist);
  asc_vf_call<main_kernel_simt_vf_2>(cce::dim3(128), out, hist);
}


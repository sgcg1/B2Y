#include <tl_templates/ascend/common.h>
#include <tl_templates/ascend/debug.h>
__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_0(__gm__ int32_t* out, __gm__ int32_t* ends, __gm__ int32_t* starts, __ubuf__ uint8_t* buf_dyn_shmem) {
  #pragma unroll
  for (int32_t i = 0; i < 16; ++i) {
    int32_t condval;
    if ((((ends[0] - starts[0]) <= 2048) && ((((i * 128) + starts[0]) + ((int32_t)threadIdx.x)) < ends[0]))) {
      condval = (((i * 128) + starts[0]) + ((int32_t)threadIdx.x));
    } else {
      condval = 16384;
    }
    out[((i * 128) + ((int32_t)threadIdx.x))] = condval;
  }
  if (((int32_t)threadIdx.x) < 7) {
    ((__ubuf__ int32_t*)buf_dyn_shmem)[(((int32_t)threadIdx.x) + 9864)] = 0;
  }
  if (((int32_t)threadIdx.x) < 3) {
    ((__ubuf__ uint32_t*)buf_dyn_shmem)[(((int32_t)threadIdx.x) + 9872)] = (uint32_t)0;
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_1(__ubuf__ uint8_t* buf_dyn_shmem, __gm__ int32_t* ends, __gm__ int32_t* starts) {
  if (((int32_t)threadIdx.x) == 0) {
    int32_t condval;
    if ((2048 < (ends[0] - starts[0]))) {
      condval = 2048;
    } else {
      condval = 0;
    }
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9864] = condval;
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_2(__ubuf__ uint8_t* buf_dyn_shmem, int32_t round) {
  #pragma unroll
  for (int32_t i = 0; i < 3; ++i) {
    if (((i * 128) + ((int32_t)threadIdx.x)) < 257) {
      ((__ubuf__ int32_t*)buf_dyn_shmem)[(((i * 128) + ((int32_t)threadIdx.x)) + 8192)] = 0;
    }
  }
  if (round == 0) {
    #pragma unroll
    for (int32_t i_1 = 0; i_1 < 8; ++i_1) {
      ((__ubuf__ int32_t*)buf_dyn_shmem)[(((i_1 * 128) + ((int32_t)threadIdx.x)) + 8449)] = 0;
    }
  }
  if (((int32_t)threadIdx.x) == 0) {
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9869] = ((__ubuf__ int32_t*)buf_dyn_shmem)[9870];
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9870] = 0;
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9866] = -1;
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9867] = 0;
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9868] = 0;
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_3(__ubuf__ uint8_t* buf_dyn_shmem, int32_t round, __gm__ int32_t* starts, __gm__ int32_t* ends, __gm__ float* x) {
    int32_t cached_count = 0;
    int32_t digit = 0;
    uint8_t digit_byte = (uint8_t)0;
    uint8_t digit_byte_1 = (uint8_t)0;
    cached_count = ((__ubuf__ int32_t*)buf_dyn_shmem)[9869];
    if ((round == 0) || (2048 < cached_count)) {
      for (int32_t tile = 0; tile < 128; ++tile) {
        asc_syncthreads();
        if (((0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9864]) && (starts[0] <= ((tile * 128) + ((int32_t)threadIdx.x)))) && (((tile * 128) + ((int32_t)threadIdx.x)) < ends[0])) {
          float value = x[((tile * 128) + ((int32_t)threadIdx.x))];
            half v_ = (half)value;
          uint16_t condval;
          if (((uint16_t)31744 < ((*(uint16_t *)(&(v_))) & (uint16_t)32767))) {
            condval = (uint16_t)65535;
          } else {
              half v__1 = (half)value;
            uint16_t condval_1;
            if ((((int32_t)((*(uint16_t *)(&(v__1))) & (uint16_t)32767)) == 0)) {
              condval_1 = (uint16_t)32768;
            } else {
                half v__2 = (half)value;
              uint16_t condval_2;
              if ((0 < ((int32_t)((*(uint16_t *)(&(v__2))) & (uint16_t)32768)))) {
                  half v__3 = (half)value;
                condval_2 = (~(*(uint16_t *)(&(v__3))));
              } else {
                  half v__4 = (half)value;
                condval_2 = ((*(uint16_t *)(&(v__4))) | (uint16_t)32768);
              }
              condval_1 = condval_2;
            }
            condval = condval_1;
          }
          uint32_t condval_3;
          if ((round == 0)) {
            condval_3 = (uint32_t)0;
          } else {
            uint32_t condval_4;
            if (((uint32_t)2139095040 < ((*(uint32_t *)(&(value))) & (uint32_t)2147483647))) {
              condval_4 = (uint32_t)4294967295;
            } else {
              uint32_t condval_5;
              if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483647) == (uint32_t)0)) {
                condval_5 = (uint32_t)2147483648;
              } else {
                uint32_t condval_6;
                if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483648) != (uint32_t)0)) {
                  condval_6 = (~(*(uint32_t *)(&(value))));
                } else {
                  condval_6 = ((*(uint32_t *)(&(value))) | (uint32_t)2147483648);
                }
                condval_5 = condval_6;
              }
              condval_4 = condval_5;
            }
            condval_3 = condval_4;
          }
          if (((round == 0) || (((int32_t)((condval >> (uint16_t)8) & (uint16_t)255)) == ((int32_t)((__ubuf__ uint32_t*)buf_dyn_shmem)[9874]))) && ((condval_3 & ((__ubuf__ uint32_t*)buf_dyn_shmem)[9873]) == ((__ubuf__ uint32_t*)buf_dyn_shmem)[9872])) {
            int32_t condval_7;
            if ((round == 0)) {
                half v__5 = (half)value;
              uint16_t condval_8;
              if (((uint16_t)31744 < ((*(uint16_t *)(&(v__5))) & (uint16_t)32767))) {
                condval_8 = (uint16_t)65535;
              } else {
                  half v__6 = (half)value;
                uint16_t condval_9;
                if ((((int32_t)((*(uint16_t *)(&(v__6))) & (uint16_t)32767)) == 0)) {
                  condval_9 = (uint16_t)32768;
                } else {
                    half v__7 = (half)value;
                  uint16_t condval_10;
                  if ((0 < ((int32_t)((*(uint16_t *)(&(v__7))) & (uint16_t)32768)))) {
                      half v__8 = (half)value;
                    condval_10 = (~(*(uint16_t *)(&(v__8))));
                  } else {
                      half v__9 = (half)value;
                    condval_10 = ((*(uint16_t *)(&(v__9))) | (uint16_t)32768);
                  }
                  condval_9 = condval_10;
                }
                condval_8 = condval_9;
              }
              condval_7 = ((int32_t)((condval_8 >> (uint16_t)8) & (uint16_t)255));
            } else {
              uint32_t condval_11;
              if (((uint32_t)2139095040 < ((*(uint32_t *)(&(value))) & (uint32_t)2147483647))) {
                condval_11 = (uint32_t)4294967295;
              } else {
                uint32_t condval_12;
                if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483647) == (uint32_t)0)) {
                  condval_12 = (uint32_t)2147483648;
                } else {
                  uint32_t condval_13;
                  if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483648) != (uint32_t)0)) {
                    condval_13 = (~(*(uint32_t *)(&(value))));
                  } else {
                    condval_13 = ((*(uint32_t *)(&(value))) | (uint32_t)2147483648);
                  }
                  condval_12 = condval_13;
                }
                condval_11 = condval_12;
              }
              condval_7 = ((int32_t)((condval_11 >> ((uint32_t)(24 - (max((round - 1), 0) * 8)))) & (uint32_t)255));
            }
            digit = condval_7;
            asc_atomic_add(            int64_t condval_14;
            if ((((int64_t)round) == (int64_t)0)) {
              condval_14 = ((((((int64_t)((int32_t)threadIdx.x)) & (int64_t)3) * (int64_t)256) + max((int64_t)0, min(((int64_t)digit), (int64_t)255))) + (int64_t)257);
            } else {
              condval_14 = max((int64_t)0, min(((int64_t)digit), (int64_t)255));
            }
(&(((__ubuf__ int32_t*)buf_dyn_shmem)[(condval_14 + (int64_t)8192)])), 1);
          }
        }
      }
    } else {
      if ((round % 2) == 0) {
        for (int32_t tile_1 = 0; tile_1 < ((min(cached_count, 2048) + 127) >> 7); ++tile_1) {
          if ((0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9864]) && (((tile_1 * 128) + ((int32_t)threadIdx.x)) < cached_count)) {
            uint32_t key = ((__ubuf__ uint32_t*)buf_dyn_shmem)[(((tile_1 * 128) + ((int32_t)threadIdx.x)) + 2048)];
            digit_byte = ((uint8_t)(key >> ((uint32_t)(32 - (round * 8)))));
            int32_t digit_1 = ((int32_t)digit_byte);
            asc_atomic_add((&(((__ubuf__ int32_t*)buf_dyn_shmem)[(digit_1 + 8192)])), 1);
          }
        }
      } else {
        for (int32_t tile_2 = 0; tile_2 < ((min(cached_count, 2048) + 127) >> 7); ++tile_2) {
          if ((0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9864]) && (((tile_2 * 128) + ((int32_t)threadIdx.x)) < cached_count)) {
            uint32_t key_1 = ((__ubuf__ uint32_t*)buf_dyn_shmem)[((tile_2 * 128) + ((int32_t)threadIdx.x))];
            digit_byte_1 = ((uint8_t)(key_1 >> ((uint32_t)(32 - (round * 8)))));
            int32_t digit_2 = ((int32_t)digit_byte_1);
            asc_atomic_add((&(((__ubuf__ int32_t*)buf_dyn_shmem)[(digit_2 + 8192)])), 1);
          }
        }
      }
    }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_4(__ubuf__ uint8_t* buf_dyn_shmem) {
  int32_t total = 0;
  #pragma unroll
  for (int32_t i = 0; i < 2; ++i) {
    total = 0;
    for (int32_t bank = 0; bank < 4; ++bank) {
      total = (total + ((__ubuf__ int32_t*)buf_dyn_shmem)[((((bank * 256) + (i * 128)) + ((int32_t)threadIdx.x)) + 8449)]);
    }
    ((__ubuf__ int32_t*)buf_dyn_shmem)[(((i * 128) + ((int32_t)threadIdx.x)) + 8192)] = total;
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_5(__ubuf__ uint8_t* buf_dyn_shmem) {
  int32_t total = 0;
  if (((int32_t)threadIdx.x) < 16) {
    total = 0;
    for (int32_t j = 0; j < 16; ++j) {
      ((__ubuf__ int32_t*)buf_dyn_shmem)[((9735 - j) - (((int32_t)threadIdx.x) * 16))] = total;
      total = (total + ((__ubuf__ int32_t*)buf_dyn_shmem)[((8447 - j) - (((int32_t)threadIdx.x) * 16))]);
    }
    ((__ubuf__ int32_t*)buf_dyn_shmem)[(((int32_t)threadIdx.x) + 9736)] = total;
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_6(__ubuf__ uint8_t* buf_dyn_shmem) {
  int32_t total = 0;
  int32_t count = 0;
  if ((((int32_t)threadIdx.x) == 0) && (0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9864])) {
    total = 0;
    for (int32_t group = 0; group < 16; ++group) {
      count = ((__ubuf__ int32_t*)buf_dyn_shmem)[(group + 9736)];
      ((__ubuf__ int32_t*)buf_dyn_shmem)[(group + 9736)] = total;
      total = (total + count);
    }
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9867] = total;
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9868] = total;
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_7(__ubuf__ uint8_t* buf_dyn_shmem) {
  int32_t before = 0;
  int32_t through = 0;
  #pragma unroll
  for (int32_t i = 0; i < 2; ++i) {
    asc_syncthreads();
    if (0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9864]) {
      before = (((__ubuf__ int32_t*)buf_dyn_shmem)[(((i * 128) + ((int32_t)threadIdx.x)) + 9480)] + ((__ubuf__ int32_t*)buf_dyn_shmem)[((((255 - ((int32_t)threadIdx.x)) >> 4) + 9736) - (i * 8))]);
      through = (before + ((__ubuf__ int32_t*)buf_dyn_shmem)[(((i * 128) + ((int32_t)threadIdx.x)) + 8192)]);
      ((__ubuf__ int32_t*)buf_dyn_shmem)[(((i * 128) + ((int32_t)threadIdx.x)) + 8192)] = before;
      if ((before <= ((__ubuf__ int32_t*)buf_dyn_shmem)[9864]) && (((__ubuf__ int32_t*)buf_dyn_shmem)[9864] < through)) {
        ((__ubuf__ int32_t*)buf_dyn_shmem)[9866] = ((i * 128) + ((int32_t)threadIdx.x));
        ((__ubuf__ int32_t*)buf_dyn_shmem)[9868] = before;
      }
    }
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_8(__ubuf__ uint8_t* buf_dyn_shmem) {
  if (((int32_t)threadIdx.x) == 0) {
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9864] = (((__ubuf__ int32_t*)buf_dyn_shmem)[9864] - ((__ubuf__ int32_t*)buf_dyn_shmem)[9868]);
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_9(__ubuf__ uint8_t* buf_dyn_shmem, int32_t round, __gm__ int32_t* starts, __gm__ int32_t* ends, __gm__ float* x, __gm__ int32_t* out) {
  int32_t cached_count = 0;
  int32_t digit = 0;
  uint8_t digit_byte = (uint8_t)0;
  uint8_t digit_byte_1 = (uint8_t)0;
  cached_count = ((__ubuf__ int32_t*)buf_dyn_shmem)[9869];
  if ((round == 0) || (2048 < cached_count)) {
    for (int32_t tile = 0; tile < 128; ++tile) {
      asc_syncthreads();
      if (((0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9867]) && (starts[0] <= ((tile * 128) + ((int32_t)threadIdx.x)))) && (((tile * 128) + ((int32_t)threadIdx.x)) < ends[0])) {
        float value = x[((tile * 128) + ((int32_t)threadIdx.x))];
          half v_ = (half)value;
        uint16_t condval;
        if (((uint16_t)31744 < ((*(uint16_t *)(&(v_))) & (uint16_t)32767))) {
          condval = (uint16_t)65535;
        } else {
            half v__1 = (half)value;
          uint16_t condval_1;
          if ((((int32_t)((*(uint16_t *)(&(v__1))) & (uint16_t)32767)) == 0)) {
            condval_1 = (uint16_t)32768;
          } else {
              half v__2 = (half)value;
            uint16_t condval_2;
            if ((0 < ((int32_t)((*(uint16_t *)(&(v__2))) & (uint16_t)32768)))) {
                half v__3 = (half)value;
              condval_2 = (~(*(uint16_t *)(&(v__3))));
            } else {
                half v__4 = (half)value;
              condval_2 = ((*(uint16_t *)(&(v__4))) | (uint16_t)32768);
            }
            condval_1 = condval_2;
          }
          condval = condval_1;
        }
        uint32_t condval_3;
        if ((round == 0)) {
          condval_3 = (uint32_t)0;
        } else {
          uint32_t condval_4;
          if (((uint32_t)2139095040 < ((*(uint32_t *)(&(value))) & (uint32_t)2147483647))) {
            condval_4 = (uint32_t)4294967295;
          } else {
            uint32_t condval_5;
            if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483647) == (uint32_t)0)) {
              condval_5 = (uint32_t)2147483648;
            } else {
              uint32_t condval_6;
              if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483648) != (uint32_t)0)) {
                condval_6 = (~(*(uint32_t *)(&(value))));
              } else {
                condval_6 = ((*(uint32_t *)(&(value))) | (uint32_t)2147483648);
              }
              condval_5 = condval_6;
            }
            condval_4 = condval_5;
          }
          condval_3 = condval_4;
        }
        if (((round == 0) || (((int32_t)((condval >> (uint16_t)8) & (uint16_t)255)) == ((int32_t)((__ubuf__ uint32_t*)buf_dyn_shmem)[9874]))) && ((condval_3 & ((__ubuf__ uint32_t*)buf_dyn_shmem)[9873]) == ((__ubuf__ uint32_t*)buf_dyn_shmem)[9872])) {
          int32_t condval_7;
          if ((round == 0)) {
              half v__5 = (half)value;
            uint16_t condval_8;
            if (((uint16_t)31744 < ((*(uint16_t *)(&(v__5))) & (uint16_t)32767))) {
              condval_8 = (uint16_t)65535;
            } else {
                half v__6 = (half)value;
              uint16_t condval_9;
              if ((((int32_t)((*(uint16_t *)(&(v__6))) & (uint16_t)32767)) == 0)) {
                condval_9 = (uint16_t)32768;
              } else {
                  half v__7 = (half)value;
                uint16_t condval_10;
                if ((0 < ((int32_t)((*(uint16_t *)(&(v__7))) & (uint16_t)32768)))) {
                    half v__8 = (half)value;
                  condval_10 = (~(*(uint16_t *)(&(v__8))));
                } else {
                    half v__9 = (half)value;
                  condval_10 = ((*(uint16_t *)(&(v__9))) | (uint16_t)32768);
                }
                condval_9 = condval_10;
              }
              condval_8 = condval_9;
            }
            condval_7 = ((int32_t)((condval_8 >> (uint16_t)8) & (uint16_t)255));
          } else {
            uint32_t condval_11;
            if (((uint32_t)2139095040 < ((*(uint32_t *)(&(value))) & (uint32_t)2147483647))) {
              condval_11 = (uint32_t)4294967295;
            } else {
              uint32_t condval_12;
              if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483647) == (uint32_t)0)) {
                condval_12 = (uint32_t)2147483648;
              } else {
                uint32_t condval_13;
                if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483648) != (uint32_t)0)) {
                  condval_13 = (~(*(uint32_t *)(&(value))));
                } else {
                  condval_13 = ((*(uint32_t *)(&(value))) | (uint32_t)2147483648);
                }
                condval_12 = condval_13;
              }
              condval_11 = condval_12;
            }
            condval_7 = ((int32_t)((condval_11 >> ((uint32_t)(24 - (max((round - 1), 0) * 8)))) & (uint32_t)255));
          }
          digit = condval_7;
          if (((__ubuf__ int32_t*)buf_dyn_shmem)[9866] < digit) {
            int32_t pos = (asc_atomic_add((&(((__ubuf__ int32_t*)buf_dyn_shmem)[(max(0, min(digit, 255)) + 8192)])), 1) + ((__ubuf__ int32_t*)buf_dyn_shmem)[9865]);
            if (pos < 2048) {
              if (0 <= pos) {
                out[pos] = ((tile * 128) + ((int32_t)threadIdx.x));
              }
            }
          } else {
            if ((digit == ((__ubuf__ int32_t*)buf_dyn_shmem)[9866]) && (0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9864])) {
              int32_t slot = asc_atomic_add((&(((__ubuf__ int32_t*)buf_dyn_shmem)[9870])), 1);
              if ((0 <= slot) && (slot < 2048)) {
                ((__ubuf__ int32_t*)buf_dyn_shmem)[((((round & 1) * 2048) + slot) + 4096)] = ((tile * 128) + ((int32_t)threadIdx.x));
                uint32_t condval_14;
                if ((round == 0)) {
                  uint32_t condval_15;
                  if (((uint32_t)2139095040 < ((*(uint32_t *)(&(value))) & (uint32_t)2147483647))) {
                    condval_15 = (uint32_t)4294967295;
                  } else {
                    uint32_t condval_16;
                    if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483647) == (uint32_t)0)) {
                      condval_16 = (uint32_t)2147483648;
                    } else {
                      uint32_t condval_17;
                      if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483648) != (uint32_t)0)) {
                        condval_17 = (~(*(uint32_t *)(&(value))));
                      } else {
                        condval_17 = ((*(uint32_t *)(&(value))) | (uint32_t)2147483648);
                      }
                      condval_16 = condval_17;
                    }
                    condval_15 = condval_16;
                  }
                  condval_14 = condval_15;
                } else {
                  uint32_t condval_18;
                  if (((uint32_t)2139095040 < ((*(uint32_t *)(&(value))) & (uint32_t)2147483647))) {
                    condval_18 = (uint32_t)4294967295;
                  } else {
                    uint32_t condval_19;
                    if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483647) == (uint32_t)0)) {
                      condval_19 = (uint32_t)2147483648;
                    } else {
                      uint32_t condval_20;
                      if ((((*(uint32_t *)(&(value))) & (uint32_t)2147483648) != (uint32_t)0)) {
                        condval_20 = (~(*(uint32_t *)(&(value))));
                      } else {
                        condval_20 = ((*(uint32_t *)(&(value))) | (uint32_t)2147483648);
                      }
                      condval_19 = condval_20;
                    }
                    condval_18 = condval_19;
                  }
                  condval_14 = condval_18;
                }
                ((__ubuf__ uint32_t*)buf_dyn_shmem)[(((round & 1) * 2048) + slot)] = condval_14;
              }
            }
          }
        }
      }
    }
  } else {
    if ((round % 2) == 0) {
      for (int32_t tile_1 = 0; tile_1 < ((min(cached_count, 2048) + 127) >> 7); ++tile_1) {
        asc_syncthreads();
        if ((0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9867]) && (((tile_1 * 128) + ((int32_t)threadIdx.x)) < cached_count)) {
          uint32_t key = ((__ubuf__ uint32_t*)buf_dyn_shmem)[(((tile_1 * 128) + ((int32_t)threadIdx.x)) + 2048)];
          int32_t candidate = ((__ubuf__ int32_t*)buf_dyn_shmem)[(((tile_1 * 128) + ((int32_t)threadIdx.x)) + 6144)];
          digit_byte = ((uint8_t)(key >> ((uint32_t)(32 - (round * 8)))));
          int32_t digit_1 = ((int32_t)digit_byte);
          if (((__ubuf__ int32_t*)buf_dyn_shmem)[9866] < digit_1) {
            int32_t pos_1 = (asc_atomic_add((&(((__ubuf__ int32_t*)buf_dyn_shmem)[(digit_1 + 8192)])), 1) + ((__ubuf__ int32_t*)buf_dyn_shmem)[9865]);
            if (pos_1 < 2048) {
              if (0 <= pos_1) {
                out[pos_1] = candidate;
              }
            }
          } else {
            if ((digit_1 == ((__ubuf__ int32_t*)buf_dyn_shmem)[9866]) && (0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9864])) {
              int32_t slot_1 = asc_atomic_add((&(((__ubuf__ int32_t*)buf_dyn_shmem)[9870])), 1);
              if ((0 <= slot_1) && (slot_1 < 2048)) {
                ((__ubuf__ int32_t*)buf_dyn_shmem)[(slot_1 + 4096)] = candidate;
                ((__ubuf__ uint32_t*)buf_dyn_shmem)[slot_1] = key;
              }
            }
          }
        }
      }
    } else {
      for (int32_t tile_2 = 0; tile_2 < ((min(cached_count, 2048) + 127) >> 7); ++tile_2) {
        asc_syncthreads();
        if ((0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9867]) && (((tile_2 * 128) + ((int32_t)threadIdx.x)) < cached_count)) {
          uint32_t key_1 = ((__ubuf__ uint32_t*)buf_dyn_shmem)[((tile_2 * 128) + ((int32_t)threadIdx.x))];
          int32_t candidate_1 = ((__ubuf__ int32_t*)buf_dyn_shmem)[(((tile_2 * 128) + ((int32_t)threadIdx.x)) + 4096)];
          digit_byte_1 = ((uint8_t)(key_1 >> ((uint32_t)(32 - (round * 8)))));
          int32_t digit_2 = ((int32_t)digit_byte_1);
          if (((__ubuf__ int32_t*)buf_dyn_shmem)[9866] < digit_2) {
            int32_t pos_2 = (asc_atomic_add((&(((__ubuf__ int32_t*)buf_dyn_shmem)[(digit_2 + 8192)])), 1) + ((__ubuf__ int32_t*)buf_dyn_shmem)[9865]);
            if (pos_2 < 2048) {
              if (0 <= pos_2) {
                out[pos_2] = candidate_1;
              }
            }
          } else {
            if ((digit_2 == ((__ubuf__ int32_t*)buf_dyn_shmem)[9866]) && (0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9864])) {
              int32_t slot_2 = asc_atomic_add((&(((__ubuf__ int32_t*)buf_dyn_shmem)[9870])), 1);
              if ((0 <= slot_2) && (slot_2 < 2048)) {
                ((__ubuf__ int32_t*)buf_dyn_shmem)[(slot_2 + 6144)] = candidate_1;
                ((__ubuf__ uint32_t*)buf_dyn_shmem)[(slot_2 + 2048)] = key_1;
              }
            }
          }
        }
      }
    }
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_10(__ubuf__ uint8_t* buf_dyn_shmem, int32_t round) {
  if (((int32_t)threadIdx.x) == 0) {
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9865] = (((__ubuf__ int32_t*)buf_dyn_shmem)[9865] + ((__ubuf__ int32_t*)buf_dyn_shmem)[9868]);
    if (0 <= ((__ubuf__ int32_t*)buf_dyn_shmem)[9866]) {
      if (round == 0) {
        ((__ubuf__ uint32_t*)buf_dyn_shmem)[9874] = ((uint32_t)((__ubuf__ int32_t*)buf_dyn_shmem)[9866]);
      } else {
        ((__ubuf__ uint32_t*)buf_dyn_shmem)[9872] = (((__ubuf__ uint32_t*)buf_dyn_shmem)[9872] | (((uint32_t)((__ubuf__ int32_t*)buf_dyn_shmem)[9866]) << ((uint32_t)(32 - (round * 8)))));
        ((__ubuf__ uint32_t*)buf_dyn_shmem)[9873] = (((__ubuf__ uint32_t*)buf_dyn_shmem)[9873] | ((uint32_t)255 << ((uint32_t)(32 - (round * 8)))));
      }
    }
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_11(__ubuf__ uint8_t* buf_dyn_shmem, __gm__ int32_t* starts, __gm__ int32_t* ends, __gm__ float* x) {
  int32_t count = 0;
  count = 0;
  for (int32_t offset = 0; offset < 128; ++offset) {
    if (((0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9864]) && (starts[0] <= ((((int32_t)threadIdx.x) * 128) + offset))) && (((((int32_t)threadIdx.x) * 128) + offset) < ends[0])) {
        float v_ = x[((((int64_t)((int32_t)threadIdx.x)) * (int64_t)128) + ((int64_t)offset))];
      uint32_t condval;
      if (((uint32_t)2139095040 < ((*(uint32_t *)(&(v_))) & (uint32_t)2147483647))) {
        condval = (uint32_t)4294967295;
      } else {
          float v__1 = x[((((int64_t)((int32_t)threadIdx.x)) * (int64_t)128) + ((int64_t)offset))];
        uint32_t condval_1;
        if ((((*(uint32_t *)(&(v__1))) & (uint32_t)2147483647) == (uint32_t)0)) {
          condval_1 = (uint32_t)2147483648;
        } else {
            float v__2 = x[((((int64_t)((int32_t)threadIdx.x)) * (int64_t)128) + ((int64_t)offset))];
          uint32_t condval_2;
          if ((((*(uint32_t *)(&(v__2))) & (uint32_t)2147483648) != (uint32_t)0)) {
              float v__3 = x[((((int64_t)((int32_t)threadIdx.x)) * (int64_t)128) + ((int64_t)offset))];
            condval_2 = (~(*(uint32_t *)(&(v__3))));
          } else {
              float v__4 = x[((((int64_t)((int32_t)threadIdx.x)) * (int64_t)128) + ((int64_t)offset))];
            condval_2 = ((*(uint32_t *)(&(v__4))) | (uint32_t)2147483648);
          }
          condval_1 = condval_2;
        }
        condval = condval_1;
      }
      if (condval == ((__ubuf__ uint32_t*)buf_dyn_shmem)[9872]) {
        count = (count + 1);
      }
    }
  }
  ((__ubuf__ int32_t*)buf_dyn_shmem)[(((int32_t)threadIdx.x) + 9736)] = count;
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_12(__ubuf__ uint8_t* buf_dyn_shmem) {
  int32_t base = 0;
  int32_t value = 0;
  if (((int32_t)threadIdx.x) == 0) {
    base = 0;
    for (int32_t i = 0; i < 128; ++i) {
      value = ((__ubuf__ int32_t*)buf_dyn_shmem)[(i + 9736)];
      ((__ubuf__ int32_t*)buf_dyn_shmem)[(i + 9736)] = base;
      base = (base + value);
    }
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_13(__ubuf__ uint8_t* buf_dyn_shmem, __gm__ int32_t* starts, __gm__ int32_t* ends, __gm__ float* x, __gm__ int32_t* out) {
  int32_t position = 0;
  position = (((__ubuf__ int32_t*)buf_dyn_shmem)[9865] + ((__ubuf__ int32_t*)buf_dyn_shmem)[(((int32_t)threadIdx.x) + 9736)]);
  for (int32_t offset = 0; offset < 128; ++offset) {
    if (((0 < ((__ubuf__ int32_t*)buf_dyn_shmem)[9864]) && (starts[0] <= ((((int32_t)threadIdx.x) * 128) + offset))) && (((((int32_t)threadIdx.x) * 128) + offset) < ends[0])) {
        float v_ = x[((((int64_t)((int32_t)threadIdx.x)) * (int64_t)128) + ((int64_t)offset))];
      uint32_t condval;
      if (((uint32_t)2139095040 < ((*(uint32_t *)(&(v_))) & (uint32_t)2147483647))) {
        condval = (uint32_t)4294967295;
      } else {
          float v__1 = x[((((int64_t)((int32_t)threadIdx.x)) * (int64_t)128) + ((int64_t)offset))];
        uint32_t condval_1;
        if ((((*(uint32_t *)(&(v__1))) & (uint32_t)2147483647) == (uint32_t)0)) {
          condval_1 = (uint32_t)2147483648;
        } else {
            float v__2 = x[((((int64_t)((int32_t)threadIdx.x)) * (int64_t)128) + ((int64_t)offset))];
          uint32_t condval_2;
          if ((((*(uint32_t *)(&(v__2))) & (uint32_t)2147483648) != (uint32_t)0)) {
              float v__3 = x[((((int64_t)((int32_t)threadIdx.x)) * (int64_t)128) + ((int64_t)offset))];
            condval_2 = (~(*(uint32_t *)(&(v__3))));
          } else {
              float v__4 = x[((((int64_t)((int32_t)threadIdx.x)) * (int64_t)128) + ((int64_t)offset))];
            condval_2 = ((*(uint32_t *)(&(v__4))) | (uint32_t)2147483648);
          }
          condval_1 = condval_2;
        }
        condval = condval_1;
      }
      if (condval == ((__ubuf__ uint32_t*)buf_dyn_shmem)[9872]) {
        if (position < (((__ubuf__ int32_t*)buf_dyn_shmem)[9865] + ((__ubuf__ int32_t*)buf_dyn_shmem)[9864])) {
          if (0 <= position) {
            if (position < 2048) {
              out[position] = ((((int32_t)threadIdx.x) * 128) + offset);
            }
          }
        }
        position = (position + 1);
      }
    }
  }
}

__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_14(__ubuf__ uint8_t* buf_dyn_shmem) {
  if (((int32_t)threadIdx.x) == 0) {
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9865] = (((__ubuf__ int32_t*)buf_dyn_shmem)[9865] + ((__ubuf__ int32_t*)buf_dyn_shmem)[9864]);
    ((__ubuf__ int32_t*)buf_dyn_shmem)[9864] = 0;
  }
}

extern "C" __global__ __vector__ void main_kernel(__gm__ int32_t* ends, __gm__ int32_t* out, __gm__ int32_t* starts, __gm__ float* x) {
  asc_init();
  __ubuf__ uint8_t *buf_dyn_shmem = (__ubuf__ uint8_t *)0;
  asc_vf_call<main_kernel_simt_vf_0>(cce::dim3(128), out, ends, starts, buf_dyn_shmem);
  asc_vf_call<main_kernel_simt_vf_1>(cce::dim3(128), buf_dyn_shmem, ends, starts);
  for (int32_t round = 0; round < 5; ++round) {
    asc_vf_call<main_kernel_simt_vf_2>(cce::dim3(128), buf_dyn_shmem, round);
    asc_vf_call<main_kernel_simt_vf_3>(cce::dim3(128), buf_dyn_shmem, round, starts, ends, x);
    if (round == 0) {
      asc_vf_call<main_kernel_simt_vf_4>(cce::dim3(128), buf_dyn_shmem);
    }
    asc_vf_call<main_kernel_simt_vf_5>(cce::dim3(128), buf_dyn_shmem);
    asc_vf_call<main_kernel_simt_vf_6>(cce::dim3(128), buf_dyn_shmem);
    asc_vf_call<main_kernel_simt_vf_7>(cce::dim3(128), buf_dyn_shmem);
    asc_vf_call<main_kernel_simt_vf_8>(cce::dim3(128), buf_dyn_shmem);
    asc_vf_call<main_kernel_simt_vf_9>(cce::dim3(128), buf_dyn_shmem, round, starts, ends, x, out);
    asc_vf_call<main_kernel_simt_vf_10>(cce::dim3(128), buf_dyn_shmem, round);
  }
  asc_vf_call<main_kernel_simt_vf_11>(cce::dim3(128), buf_dyn_shmem, starts, ends, x);
  asc_vf_call<main_kernel_simt_vf_12>(cce::dim3(128), buf_dyn_shmem);
  asc_vf_call<main_kernel_simt_vf_13>(cce::dim3(128), buf_dyn_shmem, starts, ends, x, out);
  asc_vf_call<main_kernel_simt_vf_14>(cce::dim3(128), buf_dyn_shmem);
}



"""Direct nested SIMD frequency/cumulative histogram, guarded by installed API contract."""
import tilelang
import tilelang.ascend.language as T
import tilelang.ascend.language.simd


@tilelang.jit(target="ascend",out_idx=[])
def histogram(N:int=16384,MASKED:bool=False,SEED_F:int=0,SEED_C:int=0):
    assert N==16384 and 0<=SEED_F<=11 and 0<=SEED_C<=11
    @T.prim_func
    def main(digits:T.Tensor((N,),"uint8"),tags:T.Tensor((N,),"uint8"),out:T.Tensor((4,128),"uint16")):
        with T.Kernel(1):
            data=T.alloc_shared((N,),"uint8")
            result=T.alloc_shared((4,128),"uint16")
            if MASKED:
                selected=T.alloc_shared((N,),"uint8")
                T.copy(tags,selected)
            T.copy(digits,data)
            with T.SimdVF():
                m8=T.simd.pset(8)
                m16=T.simd.pset(16)
                f0=T.simd.alloc_var("uint16")
                f1=T.simd.alloc_var("uint16")
                c0=T.simd.alloc_var("uint16")
                c1=T.simd.alloc_var("uint16")
                f0=T.simd.vdup(T.uint16(SEED_F),"uint16",m16)
                f1=T.simd.vdup(T.uint16(SEED_F),"uint16",m16)
                c0=T.simd.vdup(T.uint16(SEED_C),"uint16",m16)
                c1=T.simd.vdup(T.uint16(SEED_C),"uint16",m16)
                zero=T.simd.vdup(T.uint8(0),"uint8",m8)
                for tile in T.serial(N//256):
                    source=T.simd.vld(data[tile*256],dist="NORM")
                    if MASKED:
                        tag=T.simd.vld(selected[tile*256],dist="NORM")
                        active=T.simd.vcmp(tag,zero,m8,op="ne")
                    else:
                        active=m8
                    T.simd.dhistv2(f0,source,active,bin=0)
                    T.simd.dhistv2(f1,source,active,bin=1)
                    T.simd.chistv2(c0,source,active,bin=0)
                    T.simd.chistv2(c1,source,active,bin=1)
                T.simd.vsts(result[0,0],f0,m16,dist="NORM_B16")
                T.simd.vsts(result[1,0],f1,m16,dist="NORM_B16")
                T.simd.vsts(result[2,0],c0,m16,dist="NORM_B16")
                T.simd.vsts(result[3,0],c1,m16,dist="NORM_B16")
            T.copy(result,out)
    return main

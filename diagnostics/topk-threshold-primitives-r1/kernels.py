"""Measured concrete key/collection expressions, not an invented vector-histogram API."""
import tilelang
import tilelang.ascend.language as T


@tilelang.jit(target="ascend", out_idx=[])
def encode_keys(N: int=16384):
    def encode(value):
        bits=T.reinterpret(value,T.uint32)
        mag=bits&T.Cast(T.uint32,0x7fffffff)
        ordered=T.if_then_else(bits&T.Cast(T.uint32,0x80000000)!=0,bits^T.Cast(T.uint32,0xffffffff),bits^T.Cast(T.uint32,0x80000000))
        return T.if_then_else(mag>T.Cast(T.uint32,0x7f800000),T.Cast(T.uint32,0xffffffff),T.if_then_else(mag==0,T.Cast(T.uint32,0x80000000),ordered))
    @T.prim_func
    def main(x:T.Tensor((N,),T.float32),out:T.Tensor((N,),T.int32)):
        with T.Kernel(1):
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):
                    out[i]=T.reinterpret(encode(x[i]),T.int32)
    return main


@tilelang.jit(target="ascend", out_idx=[])
def collect_given_threshold(N: int=16384,K: int=2048):
    G,W=128,128
    assert N==G*W and K==2048
    def encode(value):
        bits=T.reinterpret(value,T.uint32)
        mag=bits&T.Cast(T.uint32,0x7fffffff)
        ordered=T.if_then_else(bits&T.Cast(T.uint32,0x80000000)!=0,bits^T.Cast(T.uint32,0xffffffff),bits^T.Cast(T.uint32,0x80000000))
        return T.if_then_else(mag>T.Cast(T.uint32,0x7f800000),T.Cast(T.uint32,0xffffffff),T.if_then_else(mag==0,T.Cast(T.uint32,0x80000000),ordered))
    @T.prim_func
    def main(x:T.Tensor((N,),T.float32),starts:T.Tensor((1,),T.int32),ends:T.Tensor((1,),T.int32),
             threshold:T.Tensor((1,),T.int32),out:T.Tensor((K,),T.int32),meta:T.Tensor((3,),T.int32)):
        with T.Kernel(1):
            raw=T.alloc_shared((N,),T.float32)
            keys=T.alloc_shared((N,),T.uint32)
            above=T.alloc_shared((G,),T.int32)
            equal=T.alloc_shared((G,),T.int32)
            base_above=T.alloc_shared((G,),T.int32)
            base_equal=T.alloc_shared((G,),T.int32)
            totals=T.alloc_shared((3,),T.int32)
            T.copy(x,raw)
            with T.SimtVF(threads=128):
                for i in T.Parallel(N):keys[i]=encode(raw[i])
                for i in T.Parallel(K):out[i]=N
            with T.SimtVF(threads=128):
                for group in T.Parallel(G):
                    a=T.alloc_var(T.int32)
                    e=T.alloc_var(T.int32)
                    a=0
                    e=0
                    for j in T.serial(W):
                        i=group*W+j
                        if starts[0]<=i and i<ends[0]:
                            key=keys[T.max(0,T.min(i,N-1))]
                            pivot=T.reinterpret(threshold[0],T.uint32)
                            if key>pivot:a=a+1
                            if key==pivot:e=e+1
                    above[group]=a
                    equal[group]=e
            with T.SimtVF(threads=128):
                for thread in T.Parallel(128):
                    if thread==0:
                        a=T.alloc_var(T.int32)
                        e=T.alloc_var(T.int32)
                        a=0
                        e=0
                        for group in T.serial(G):
                            base_above[group]=a
                            base_equal[group]=e
                            a=a+above[group]
                            e=e+equal[group]
                        totals[0]=a
                        totals[1]=e
                        totals[2]=T.min(e,T.max(0,K-a))
                        meta[0]=a
                        meta[1]=e
                        meta[2]=T.min(e,T.max(0,K-a))
            with T.SimtVF(threads=128):
                for group in T.Parallel(G):
                    a=T.alloc_var(T.int32)
                    e=T.alloc_var(T.int32)
                    a=0
                    e=0
                    for j in T.serial(W):
                        i=group*W+j
                        if starts[0]<=i and i<ends[0]:
                            key=keys[T.max(0,T.min(i,N-1))]
                            pivot=T.reinterpret(threshold[0],T.uint32)
                            if key>pivot:
                                pos=base_above[group]+a
                                if pos<K:out[T.max(0,T.min(pos,K-1))]=i
                                a=a+1
                            if key==pivot:
                                if base_equal[group]+e<totals[2]:
                                    pos=totals[0]+base_equal[group]+e
                                    if pos<K:out[T.max(0,T.min(pos,K-1))]=i
                                e=e+1
    return main

module {
  func.func @main(%arg0: memref<?xbf16>, %arg1: memref<?xbf16>, %arg2: memref<?xf32>, %arg3: memref<?xi32>, %arg4: memref<?xf32>, %arg5: i32, %arg6: i32) attributes {BlockIdx = 5 : i64, SubBlockIdx = 6 : i64} {
    %reinterpret_cast = memref.reinterpret_cast %arg0 to offset: [0], sizes: [1, 4096, 64, 256], strides: [67108864, 16384, 256, 1] : memref<?xbf16> to memref<1x4096x64x256xbf16, strided<[67108864, 16384, 256, 1]>>
    %reinterpret_cast_0 = memref.reinterpret_cast %arg1 to offset: [0], sizes: [1, 4096, 256], strides: [1048576, 256, 1] : memref<?xbf16> to memref<1x4096x256xbf16, strided<[1048576, 256, 1]>>
    %reinterpret_cast_1 = memref.reinterpret_cast %arg2 to offset: [0], sizes: [64], strides: [1] : memref<?xf32> to memref<64xf32, strided<[1]>>
    %reinterpret_cast_2 = memref.reinterpret_cast %arg3 to offset: [0], sizes: [1, 4096, 128], strides: [524288, 128, 1] : memref<?xi32> to memref<1x4096x128xi32, strided<[524288, 128, 1]>>
    %reinterpret_cast_3 = memref.reinterpret_cast %arg4 to offset: [0], sizes: [1, 4096, 64, 256], strides: [67108864, 16384, 256, 1] : memref<?xf32> to memref<1x4096x64x256xf32, strided<[67108864, 16384, 256, 1]>>
    %alloc = memref.alloc() : memref<32768xi8, 1>
    %c0 = arith.constant 0 : index
    %view = memref.view %alloc[%c0][] : memref<32768xi8, 1> to memref<64x256xbf16, 1>
    %alloc_4 = memref.alloc() : memref<32768xi8, 1>
    %c0_5 = arith.constant 0 : index
    %view_6 = memref.view %alloc_4[%c0_5][] : memref<32768xi8, 1> to memref<64x256xbf16, 1>
    %alloc_7 = memref.alloc() : memref<8192xi8, 1>
    %c0_8 = arith.constant 0 : index
    %view_9 = memref.view %alloc_7[%c0_8][] : memref<8192xi8, 1> to memref<64x64xbf16, 1>
    %alloc_10 = memref.alloc() : memref<256xi8, 1>
    %c0_11 = arith.constant 0 : index
    %view_12 = memref.view %alloc_10[%c0_11][] : memref<256xi8, 1> to memref<64xf32, 1>
    %alloc_13 = memref.alloc() : memref<256xi8, 1>
    %c0_14 = arith.constant 0 : index
    %view_15 = memref.view %alloc_13[%c0_14][] : memref<256xi8, 1> to memref<64xi32, 1>
    %alloc_16 = memref.alloc() : memref<32768xi8, 1>
    %c0_17 = arith.constant 0 : index
    %view_18 = memref.view %alloc_16[%c0_17][] : memref<32768xi8, 1> to memref<64x256xbf16, 1>
    %alloc_19 = memref.alloc() : memref<64x64xf32, 2>
    %alloc_20 = memref.alloc() : memref<64x256xf32, 2>
    %alloc_21 = memref.alloc() : memref<8192xi8, 1>
    %c0_22 = arith.constant 0 : index
    %view_23 = memref.view %alloc_21[%c0_22][] : memref<8192xi8, 1> to memref<32x64xf32, 1>
    %alloc_24 = memref.alloc() : memref<4096xi8, 1>
    %c0_25 = arith.constant 0 : index
    %view_26 = memref.view %alloc_24[%c0_25][] : memref<4096xi8, 1> to memref<32x64xbf16, 1>
    %alloc_27 = memref.alloc() : memref<8192xi8, 1>
    %c0_28 = arith.constant 0 : index
    %view_29 = memref.view %alloc_27[%c0_28][] : memref<8192xi8, 1> to memref<32x64xf32, 1>
    %alloc_30 = memref.alloc() : memref<32768xi8, 1>
    %c0_31 = arith.constant 0 : index
    %view_32 = memref.view %alloc_30[%c0_31][] : memref<32768xi8, 1> to memref<32x256xf32, 1>
    %alloc_33 = memref.alloc() : memref<32768xi8, 1>
    %c0_34 = arith.constant 0 : index
    %view_35 = memref.view %alloc_33[%c0_34][] : memref<32768xi8, 1> to memref<32x256xf32, 1>
    %alloc_36 = memref.alloc() : memref<128xi8, 1>
    %c0_37 = arith.constant 0 : index
    %view_38 = memref.view %alloc_36[%c0_37][] : memref<128xi8, 1> to memref<32xf32, 1>
    %alloc_39 = memref.alloc() : memref<128xi8, 1>
    %c0_40 = arith.constant 0 : index
    %view_41 = memref.view %alloc_39[%c0_40][] : memref<128xi8, 1> to memref<32xf32, 1>
    %alloc_42 = memref.alloc() : memref<128xi8, 1>
    %c0_43 = arith.constant 0 : index
    %view_44 = memref.view %alloc_42[%c0_43][] : memref<128xi8, 1> to memref<32xf32, 1>
    %alloc_45 = memref.alloc() : memref<128xi8, 1>
    %c0_46 = arith.constant 0 : index
    %view_47 = memref.view %alloc_45[%c0_46][] : memref<128xi8, 1> to memref<32xf32, 1>
    %alloc_48 = memref.alloc() : memref<128xi8, 1>
    %c0_49 = arith.constant 0 : index
    %view_50 = memref.view %alloc_48[%c0_49][] : memref<128xi8, 1> to memref<32xf32, 1>
    %c0_i32 = arith.constant 0 : i32
    %0 = arith.index_cast %c0_i32 : i32 to index
    %c0_i32_51 = arith.constant 0 : i32
    %1 = arith.index_cast %c0_i32_51 : i32 to index
    %c67108864 = arith.constant 67108864 : index
    %2 = arith.muli %1, %c67108864 : index
    %3 = arith.addi %0, %2 : index
    %4 = arith.index_cast %arg5 : i32 to index
    %c16384 = arith.constant 16384 : index
    %5 = arith.muli %4, %c16384 : index
    %6 = arith.addi %3, %5 : index
    %c0_i32_52 = arith.constant 0 : i32
    %7 = arith.index_cast %c0_i32_52 : i32 to index
    %c256 = arith.constant 256 : index
    %8 = arith.muli %7, %c256 : index
    %9 = arith.addi %6, %8 : index
    %c0_i32_53 = arith.constant 0 : i32
    %10 = arith.index_cast %c0_i32_53 : i32 to index
    %c1 = arith.constant 1 : index
    %11 = arith.muli %10, %c1 : index
    %12 = arith.addi %9, %11 : index
    %reinterpret_cast_54 = memref.reinterpret_cast %reinterpret_cast to offset: [%12], sizes: [64, 256], strides: [256, 1] : memref<1x4096x64x256xbf16, strided<[67108864, 16384, 256, 1]>> to memref<64x256xbf16, strided<[256, 1], offset: ?>>
    "tilelang.copy"(%reinterpret_cast_54, %view) : (memref<64x256xbf16, strided<[256, 1], offset: ?>>, memref<64x256xbf16, 1>) -> ()
    "tilelang.scope"() ({
      %cst = arith.constant 0.000000e+00 : f32
      linalg.fill ins(%cst : f32) outs(%view_32 : memref<32x256xf32, 1>)
      %cst_69 = arith.constant 1.000000e+00 : f32
      linalg.fill ins(%cst_69 : f32) outs(%view_47 : memref<32xf32, 1>)
    }) {mode = #tilelang.scope_mode<simd>} : () -> ()
    %c0_i32_55 = arith.constant 0 : i32
    %13 = arith.index_cast %c0_i32_55 : i32 to index
    %c32_i32 = arith.constant 32 : i32
    %14 = arith.muli %arg6, %c32_i32 : i32
    %15 = arith.index_cast %14 : i32 to index
    %c1_56 = arith.constant 1 : index
    %16 = arith.muli %15, %c1_56 : index
    %17 = arith.addi %13, %16 : index
    %reinterpret_cast_57 = memref.reinterpret_cast %reinterpret_cast_1 to offset: [%17], sizes: [32], strides: [1] : memref<64xf32, strided<[1]>> to memref<32xf32, strided<[1], offset: ?>>
    "tilelang.copy"(%reinterpret_cast_57, %view_38) : (memref<32xf32, strided<[1], offset: ?>>, memref<32xf32, 1>) -> ()
    %c0_i32_58 = arith.constant 0 : i32
    %18 = arith.index_cast %c0_i32_58 : i32 to index
    %c2_i32 = arith.constant 2 : i32
    %19 = arith.index_cast %c2_i32 : i32 to index
    %20 = arith.addi %18, %19 : index
    %c1_59 = arith.constant 1 : index
    scf.for %arg7 = %18 to %20 step %c1_59 {
      %c0_i32_69 = arith.constant 0 : i32
      %35 = arith.index_cast %c0_i32_69 : i32 to index
      %c64_i32 = arith.constant 64 : i32
      %36 = arith.index_cast %c64_i32 : i32 to index
      %37 = arith.addi %35, %36 : index
      %c1_70 = arith.constant 1 : index
      scf.for %arg8 = %35 to %37 step %c1_70 {
        %c0_i32_77 = arith.constant 0 : i32
        %44 = arith.index_cast %c0_i32_77 : i32 to index
        %45 = arith.index_cast %arg5 : i32 to index
        %c64_i32_78 = arith.constant 64 : i32
        %46 = arith.index_cast %c64_i32_78 : i32 to index
        %47 = arith.muli %arg7, %46 : index
        %48 = arith.addi %47, %arg8 : index
        %49 = memref.load %reinterpret_cast_2[%44, %45, %48] : memref<1x4096x128xi32, strided<[524288, 128, 1]>>
        memref.store %49, %view_15[%arg8] : memref<64xi32, 1>
      } {tilelang.loop_kind = "serial"}
      %c0_i32_71 = arith.constant 0 : i32
      %38 = arith.index_cast %c0_i32_71 : i32 to index
      %c64_i32_72 = arith.constant 64 : i32
      %39 = arith.index_cast %c64_i32_72 : i32 to index
      %40 = arith.addi %38, %39 : index
      %c1_73 = arith.constant 1 : index
      scf.for %arg8 = %38 to %40 step %c1_73 {
        %44 = memref.load %view_15[%arg8] : memref<64xi32, 1>
        %c-1_i32 = arith.constant -1 : i32
        %45 = arith.cmpi ne, %44, %c-1_i32 : i32
        scf.if %45 {
          %cst = arith.constant 1.000000e+00 : f32
          memref.store %cst, %view_12[%arg8] : memref<64xf32, 1>
        } else {
          %cst = arith.constant 0.000000e+00 : f32
          memref.store %cst, %view_12[%arg8] : memref<64xf32, 1>
        }
      } {tilelang.loop_kind = "serial"}
      "tilelang.scope"() ({
        %cst = arith.constant 0.000000e+00 : bf16
        linalg.fill ins(%cst : bf16) outs(%view_18 : memref<64x256xbf16, 1>)
      }) {mode = #tilelang.scope_mode<simd>} : () -> ()
      %c0_i32_74 = arith.constant 0 : i32
      %41 = arith.index_cast %c0_i32_74 : i32 to index
      %c64_i32_75 = arith.constant 64 : i32
      %42 = arith.index_cast %c64_i32_75 : i32 to index
      %43 = arith.addi %41, %42 : index
      %c1_76 = arith.constant 1 : index
      scf.for %arg8 = %41 to %43 step %c1_76 {
        %44 = memref.load %view_15[%arg8] : memref<64xi32, 1>
        %c-1_i32 = arith.constant -1 : i32
        %45 = arith.cmpi ne, %44, %c-1_i32 : i32
        scf.if %45 {
          %c0_i32_77 = arith.constant 0 : i32
          %46 = arith.index_cast %c0_i32_77 : i32 to index
          %c0_i32_78 = arith.constant 0 : i32
          %47 = arith.index_cast %c0_i32_78 : i32 to index
          %c1048576 = arith.constant 1048576 : index
          %48 = arith.muli %47, %c1048576 : index
          %49 = arith.addi %46, %48 : index
          %50 = memref.load %view_15[%arg8] : memref<64xi32, 1>
          %51 = arith.index_cast %50 : i32 to index
          %c256_79 = arith.constant 256 : index
          %52 = arith.muli %51, %c256_79 : index
          %53 = arith.addi %49, %52 : index
          %c0_i32_80 = arith.constant 0 : i32
          %54 = arith.index_cast %c0_i32_80 : i32 to index
          %c1_81 = arith.constant 1 : index
          %55 = arith.muli %54, %c1_81 : index
          %56 = arith.addi %53, %55 : index
          %reinterpret_cast_82 = memref.reinterpret_cast %reinterpret_cast_0 to offset: [%56], sizes: [256], strides: [1] : memref<1x4096x256xbf16, strided<[1048576, 256, 1]>> to memref<256xbf16, strided<[1], offset: ?>>
          %c0_i32_83 = arith.constant 0 : i32
          %57 = arith.index_cast %c0_i32_83 : i32 to index
          %c256_84 = arith.constant 256 : index
          %58 = arith.muli %arg8, %c256_84 : index
          %59 = arith.addi %57, %58 : index
          %c0_i32_85 = arith.constant 0 : i32
          %60 = arith.index_cast %c0_i32_85 : i32 to index
          %c1_86 = arith.constant 1 : index
          %61 = arith.muli %60, %c1_86 : index
          %62 = arith.addi %59, %61 : index
          %reinterpret_cast_87 = memref.reinterpret_cast %view_18 to offset: [%62], sizes: [256], strides: [1] : memref<64x256xbf16, 1> to memref<256xbf16, strided<[1], offset: ?>, 1>
          "tilelang.copy"(%reinterpret_cast_82, %reinterpret_cast_87) : (memref<256xbf16, strided<[1], offset: ?>>, memref<256xbf16, strided<[1], offset: ?>, 1>) -> ()
        }
      } {tilelang.loop_kind = "serial"}
      "tilelang.copy"(%view_18, %view_6) : (memref<64x256xbf16, 1>, memref<64x256xbf16, 1>) -> ()
      "tilelang.gemm"(%view, %view_6, %alloc_19) {clear_accum, transpose_b} : (memref<64x256xbf16, 1>, memref<64x256xbf16, 1>, memref<64x64xf32, 2>) -> ()
      "tilelang.copy"(%alloc_19, %view_23) {split_dim = 0 : i64} : (memref<64x64xf32, 2>, memref<32x64xf32, 1>) -> ()
      "tilelang.scope"() ({
        %alloc_77 = memref.alloc() : memref<32x64xf32, 2>
        %alloc_78 = memref.alloc() : memref<32xf32, 2>
        "tilelang.copy"(%view_23, %alloc_77) : (memref<32x64xf32, 1>, memref<32x64xf32, 2>) -> ()
        %cst = arith.constant 6.250000e-02 : f32
        "tilelang.vmuls"(%alloc_77, %cst, %alloc_77) : (memref<32x64xf32, 2>, f32, memref<32x64xf32, 2>) -> ()
        "tilelang.copy"(%alloc_77, %view_23) : (memref<32x64xf32, 2>, memref<32x64xf32, 1>) -> ()
        "tilelang.copy"(%view_38, %view_41) : (memref<32xf32, 1>, memref<32xf32, 1>) -> ()
        %cst_79 = arith.constant 0xFF800000 : f32
        linalg.fill ins(%cst_79 : f32) outs(%alloc_78 : memref<32xf32, 2>)
        linalg.reduce ins(%alloc_77 : memref<32x64xf32, 2>) outs(%alloc_78 : memref<32xf32, 2>) dimensions = [1] 
          (%in: f32, %init: f32) {
            %44 = arith.maximumf %in, %init : f32
            linalg.yield %44 : f32
          }
        "tilelang.copy"(%alloc_78, %view_38) : (memref<32xf32, 2>, memref<32xf32, 1>) -> ()
      }) {mode = #tilelang.scope_mode<simd>} : () -> ()
      "tilelang.scope"() ({
        %alloc_77 = memref.alloc() : memref<32x64xf32, 2>
        %alloc_78 = memref.alloc() : memref<32x64xf32, 2>
        %alloc_79 = memref.alloc() : memref<32x64xbf16, 2>
        %alloc_80 = memref.alloc() : memref<32xf32, 2>
        %alloc_81 = memref.alloc() : memref<32xf32, 2>
        %alloc_82 = memref.alloc() : memref<32xf32, 2>
        %alloc_83 = memref.alloc() : memref<32x64xf32, 2>
        %alloc_84 = memref.alloc() : memref<64xf32, 2>
        %alloc_85 = memref.alloc() : memref<32x64xf32, 2>
        "tilelang.copy"(%view_23, %alloc_77) : (memref<32x64xf32, 1>, memref<32x64xf32, 2>) -> ()
        "tilelang.copy"(%view_38, %alloc_82) : (memref<32xf32, 1>, memref<32xf32, 2>) -> ()
        "tilelang.copy"(%view_41, %alloc_80) : (memref<32xf32, 1>, memref<32xf32, 2>) -> ()
        "tilelang.vmax"(%alloc_82, %alloc_80, %alloc_81) {dtype = "float32"} : (memref<32xf32, 2>, memref<32xf32, 2>, memref<32xf32, 2>) -> ()
        "tilelang.copy"(%alloc_81, %view_38) : (memref<32xf32, 2>, memref<32xf32, 1>) -> ()
        linalg.broadcast ins(%alloc_81 : memref<32xf32, 2>) outs(%alloc_83 : memref<32x64xf32, 2>) dimensions = [1] 
        "tilelang.vexpdif"(%alloc_77, %alloc_83, %alloc_78) : (memref<32x64xf32, 2>, memref<32x64xf32, 2>, memref<32x64xf32, 2>) -> ()
        "tilelang.copy"(%view_12, %alloc_84) : (memref<64xf32, 1>, memref<64xf32, 2>) -> ()
        linalg.broadcast ins(%alloc_84 : memref<64xf32, 2>) outs(%alloc_85 : memref<32x64xf32, 2>) dimensions = [0] 
        linalg.mul ins(%alloc_78, %alloc_85 : memref<32x64xf32, 2>, memref<32x64xf32, 2>) outs(%alloc_78 : memref<32x64xf32, 2>)
        "tilelang.vcvt"(%alloc_78, %alloc_79) {dst_dtype = "bfloat16", src_dtype = "float32"} : (memref<32x64xf32, 2>, memref<32x64xbf16, 2>) -> ()
        "tilelang.copy"(%alloc_79, %view_26) : (memref<32x64xbf16, 2>, memref<32x64xbf16, 1>) -> ()
        "tilelang.copy"(%alloc_78, %view_29) : (memref<32x64xf32, 2>, memref<32x64xf32, 1>) -> ()
      }) {mode = #tilelang.scope_mode<simd>} : () -> ()
      "tilelang.copy"(%view_26, %view_9) {split_dim = 0 : i64} : (memref<32x64xbf16, 1>, memref<64x64xbf16, 1>) -> ()
      "tilelang.scope"() ({
        %alloc_77 = memref.alloc() : memref<32x64xf32, 2>
        %alloc_78 = memref.alloc() : memref<32xf32, 2>
        "tilelang.copy"(%view_29, %alloc_77) : (memref<32x64xf32, 1>, memref<32x64xf32, 2>) -> ()
        %cst = arith.constant 0.000000e+00 : f32
        linalg.fill ins(%cst : f32) outs(%alloc_78 : memref<32xf32, 2>)
        linalg.reduce ins(%alloc_77 : memref<32x64xf32, 2>) outs(%alloc_78 : memref<32xf32, 2>) dimensions = [1] 
          (%in: f32, %init: f32) {
            %44 = arith.addf %in, %init : f32
            linalg.yield %44 : f32
          }
        "tilelang.copy"(%alloc_78, %view_44) : (memref<32xf32, 2>, memref<32xf32, 1>) -> ()
      }) {mode = #tilelang.scope_mode<simd>} : () -> ()
      "tilelang.scope"() ({
        %alloc_77 = memref.alloc() : memref<32xf32, 2>
        %alloc_78 = memref.alloc() : memref<32xf32, 2>
        %alloc_79 = memref.alloc() : memref<32xf32, 2>
        %alloc_80 = memref.alloc() : memref<32xf32, 2>
        %alloc_81 = memref.alloc() : memref<32xf32, 2>
        "tilelang.copy"(%view_41, %alloc_77) : (memref<32xf32, 1>, memref<32xf32, 2>) -> ()
        "tilelang.copy"(%view_38, %alloc_78) : (memref<32xf32, 1>, memref<32xf32, 2>) -> ()
        "tilelang.copy"(%view_47, %alloc_79) : (memref<32xf32, 1>, memref<32xf32, 2>) -> ()
        "tilelang.copy"(%view_44, %alloc_81) : (memref<32xf32, 1>, memref<32xf32, 2>) -> ()
        "tilelang.vexpdif"(%alloc_77, %alloc_78, %alloc_80) : (memref<32xf32, 2>, memref<32xf32, 2>, memref<32xf32, 2>) -> ()
        "tilelang.copy"(%alloc_80, %view_50) : (memref<32xf32, 2>, memref<32xf32, 1>) -> ()
        linalg.mul ins(%alloc_79, %alloc_80 : memref<32xf32, 2>, memref<32xf32, 2>) outs(%alloc_79 : memref<32xf32, 2>)
        linalg.add ins(%alloc_79, %alloc_81 : memref<32xf32, 2>, memref<32xf32, 2>) outs(%alloc_79 : memref<32xf32, 2>)
        "tilelang.copy"(%alloc_79, %view_47) : (memref<32xf32, 2>, memref<32xf32, 1>) -> ()
      }) {mode = #tilelang.scope_mode<simd>} : () -> ()
      "tilelang.gemm"(%view_9, %view_6, %alloc_20) {clear_accum} : (memref<64x64xbf16, 1>, memref<64x256xbf16, 1>, memref<64x256xf32, 2>) -> ()
      "tilelang.copy"(%alloc_20, %view_35) {split_dim = 0 : i64} : (memref<64x256xf32, 2>, memref<32x256xf32, 1>) -> ()
      "tilelang.scope"() ({
        %alloc_77 = memref.alloc() : memref<32x256xf32, 2>
        %alloc_78 = memref.alloc() : memref<32x256xf32, 2>
        %alloc_79 = memref.alloc() : memref<32xf32, 2>
        %alloc_80 = memref.alloc() : memref<32x256xf32, 2>
        "tilelang.copy"(%view_32, %alloc_77) : (memref<32x256xf32, 1>, memref<32x256xf32, 2>) -> ()
        "tilelang.copy"(%view_35, %alloc_78) : (memref<32x256xf32, 1>, memref<32x256xf32, 2>) -> ()
        "tilelang.copy"(%view_50, %alloc_79) : (memref<32xf32, 1>, memref<32xf32, 2>) -> ()
        linalg.broadcast ins(%alloc_79 : memref<32xf32, 2>) outs(%alloc_80 : memref<32x256xf32, 2>) dimensions = [1] 
        linalg.mul ins(%alloc_77, %alloc_80 : memref<32x256xf32, 2>, memref<32x256xf32, 2>) outs(%alloc_77 : memref<32x256xf32, 2>)
        linalg.add ins(%alloc_77, %alloc_78 : memref<32x256xf32, 2>, memref<32x256xf32, 2>) outs(%alloc_77 : memref<32x256xf32, 2>)
        "tilelang.copy"(%alloc_77, %view_32) : (memref<32x256xf32, 2>, memref<32x256xf32, 1>) -> ()
      }) {mode = #tilelang.scope_mode<simd>} : () -> ()
    } {num_stages = 2 : i64, tilelang.loop_kind = "pipelined"}
    "tilelang.scope"() ({
      %alloc_69 = memref.alloc() : memref<32x256xf32, 2>
      %alloc_70 = memref.alloc() : memref<32xf32, 2>
      %alloc_71 = memref.alloc() : memref<32x256xf32, 2>
      "tilelang.copy"(%view_32, %alloc_69) : (memref<32x256xf32, 1>, memref<32x256xf32, 2>) -> ()
      "tilelang.copy"(%view_47, %alloc_70) : (memref<32xf32, 1>, memref<32xf32, 2>) -> ()
      linalg.broadcast ins(%alloc_70 : memref<32xf32, 2>) outs(%alloc_71 : memref<32x256xf32, 2>) dimensions = [1] 
      linalg.div ins(%alloc_69, %alloc_71 : memref<32x256xf32, 2>, memref<32x256xf32, 2>) outs(%alloc_69 : memref<32x256xf32, 2>)
      "tilelang.copy"(%alloc_69, %view_32) : (memref<32x256xf32, 2>, memref<32x256xf32, 1>) -> ()
    }) {mode = #tilelang.scope_mode<simd>} : () -> ()
    %c0_i32_60 = arith.constant 0 : i32
    %21 = arith.index_cast %c0_i32_60 : i32 to index
    %c0_i32_61 = arith.constant 0 : i32
    %22 = arith.index_cast %c0_i32_61 : i32 to index
    %c67108864_62 = arith.constant 67108864 : index
    %23 = arith.muli %22, %c67108864_62 : index
    %24 = arith.addi %21, %23 : index
    %25 = arith.index_cast %arg5 : i32 to index
    %c16384_63 = arith.constant 16384 : index
    %26 = arith.muli %25, %c16384_63 : index
    %27 = arith.addi %24, %26 : index
    %c32_i32_64 = arith.constant 32 : i32
    %28 = arith.muli %arg6, %c32_i32_64 : i32
    %29 = arith.index_cast %28 : i32 to index
    %c256_65 = arith.constant 256 : index
    %30 = arith.muli %29, %c256_65 : index
    %31 = arith.addi %27, %30 : index
    %c0_i32_66 = arith.constant 0 : i32
    %32 = arith.index_cast %c0_i32_66 : i32 to index
    %c1_67 = arith.constant 1 : index
    %33 = arith.muli %32, %c1_67 : index
    %34 = arith.addi %31, %33 : index
    %reinterpret_cast_68 = memref.reinterpret_cast %reinterpret_cast_3 to offset: [%34], sizes: [32, 256], strides: [256, 1] : memref<1x4096x64x256xf32, strided<[67108864, 16384, 256, 1]>> to memref<32x256xf32, strided<[256, 1], offset: ?>>
    "tilelang.copy"(%view_32, %reinterpret_cast_68) : (memref<32x256xf32, 1>, memref<32x256xf32, strided<[256, 1], offset: ?>>) -> ()
    return
  }
}

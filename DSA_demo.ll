; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"
target triple = "hiipu64-hisilicon-cce"

define dso_local ptc_kernel void @main_mix_aic(ptr addrspace(1) %0, ptr addrspace(1) %1, ptr addrspace(1) %2, ptr addrspace(1) %3, ptr addrspace(1) %4, i32 %5, i32 %6) #0 {
  %8 = call i64 @llvm.hivm.GET.CTRL()
  %9 = call i64 @llvm.hivm.SBITSET0(i64 %8, i64 60)
  call void @llvm.hivm.SET.CTRL(i64 %9)
  %10 = call i64 @llvm.hivm.GET.CTRL()
  %11 = call i64 @llvm.hivm.SBITSET1(i64 %10, i64 48)
  call void @llvm.hivm.SET.CTRL(i64 %11)
  %12 = call i64 @llvm.hivm.GET.BLOCK.IDX()
  %13 = trunc i64 %12 to i32
  %14 = sext i32 %13 to i64
  %15 = mul i64 %14, 16384
  call void @llvm.hivm.SET.MTE2.NZ.PARA(i64 274877972481)
  %16 = ptrtoint ptr addrspace(1) %0 to i64
  %17 = mul i64 %15, 2
  %18 = add i64 %16, %17
  %19 = inttoptr i64 %18 to ptr addrspace(1)
  call void @llvm.hivm.MOV.OUT.TO.L1.MULTI.ND2NZ.U16.V310(ptr addrspace(2) inttoptr (i64 32768 to ptr addrspace(2)), ptr addrspace(1) %19, i64 18014398509490176, i64 256)
  call void @llvm.hivm.SET.FLAG.IMM(i64 4, i64 3, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 4, i64 3, i64 0)
  call void @llvm.hivm.SET.FLAG.IMM(i64 10, i64 2, i64 0)
  call void @llvm.hivm.SET.FLAG.IMM(i64 2, i64 3, i64 0)
  call void @llvm.hivm.SET.FLAG.IMM(i64 2, i64 3, i64 1)
  call void @llvm.hivm.SET.FLAG.IMM(i64 10, i64 2, i64 1)
  br label %20

20:                                               ; preds = %23, %7
  %21 = phi i64 [ %24, %23 ], [ 0, %7 ]
  %22 = icmp slt i64 %21, 2
  br i1 %22, label %23, label %25

23:                                               ; preds = %20
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 2, i64 3, i64 0)
  call void @llvm.hivm.LOAD.L1.TO.L0A.2Dv2.bf16(ptr addrspace(3) null, ptr addrspace(2) inttoptr (i64 32768 to ptr addrspace(2)), i64 17609365913600, i64 262148, i64 0)
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 3, i64 0)
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 3, i64 16)
  call void @llvm.hivm.LOAD.L1.TO.L0B.2Dv2.bf16(ptr addrspace(4) null, ptr addrspace(2) null, i64 17609365913600, i64 262148, i64 0)
  call void @llvm.hivm.SET.FLAG.IMM(i64 3, i64 2, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 3, i64 2, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 10, i64 2, i64 0)
  call void @llvm.hivm.MAD.bf162f32.c310(ptr addrspace(5) inttoptr (i64 65536 to ptr addrspace(5)), ptr addrspace(3) null, ptr addrspace(4) null, i64 -6917529026566291392)
  call void @llvm.hivm.SET.FLAG.IMM(i64 2, i64 3, i64 0)
  call void @llvm.hivm.SET.FLAG.IMM(i64 2, i64 10, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 2, i64 10, i64 0)
  call void @llvm.hivm.SET.LOOP3.PARA(i64 1)
  call void @llvm.hivm.FIX.L0C.TO.UB.f32.EXT(ptr addrspace(6) inttoptr (i64 131584 to ptr addrspace(6)), ptr addrspace(5) inttoptr (i64 65536 to ptr addrspace(5)), i64 274882102272, i64 8796093087808)
  call void @llvm.hivm.SET.FLAG.IMM(i64 10, i64 2, i64 0)
  call void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64 10, i64 4)
  call void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64 10, i64 20)
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 3, i64 1)
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 3, i64 17)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 2, i64 3, i64 1)
  call void @llvm.hivm.LOAD.L1.TO.L0A.2Dv2.bf16(ptr addrspace(3) inttoptr (i64 32768 to ptr addrspace(3)), ptr addrspace(2) inttoptr (i64 65536 to ptr addrspace(2)), i64 4415226380288, i64 262148, i64 0)
  call void @llvm.hivm.LOAD.L1.TO.L0B.2Dv2.bf16(ptr addrspace(4) inttoptr (i64 32768 to ptr addrspace(4)), ptr addrspace(2) null, i64 17609365913600, i64 1048580, i64 1)
  call void @llvm.hivm.SET.FLAG.IMM(i64 3, i64 2, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 3, i64 2, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 10, i64 2, i64 1)
  call void @llvm.hivm.MAD.bf162f32.c310(ptr addrspace(5) null, ptr addrspace(3) inttoptr (i64 32768 to ptr addrspace(3)), ptr addrspace(4) inttoptr (i64 32768 to ptr addrspace(4)), i64 -6917529023345852352)
  call void @llvm.hivm.SET.FLAG.IMM(i64 2, i64 3, i64 1)
  call void @llvm.hivm.SET.FLAG.IMM(i64 2, i64 10, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 2, i64 10, i64 0)
  call void @llvm.hivm.SET.LOOP3.PARA(i64 1)
  call void @llvm.hivm.FIX.L0C.TO.UB.f32.EXT(ptr addrspace(6) inttoptr (i64 98816 to ptr addrspace(6)), ptr addrspace(5) null, i64 1099515826176, i64 8796093087808)
  call void @llvm.hivm.SET.FLAG.IMM(i64 10, i64 2, i64 1)
  call void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64 10, i64 5)
  call void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64 10, i64 21)
  call void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64 10, i64 2)
  call void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64 10, i64 18)
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 3, i64 2)
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 3, i64 18)
  %24 = add i64 %21, 1
  br label %20

25:                                               ; preds = %20
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 10, i64 2, i64 1)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 2, i64 3, i64 1)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 2, i64 3, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 10, i64 2, i64 0)
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 10, i64 3)
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 10, i64 19)
  call void @llvm.hivm.BARRIER(i64 6)
  ret void
}

define dso_local ptc_kernel void @main_mix_aiv(ptr addrspace(1) %0, ptr addrspace(1) %1, ptr addrspace(1) %2, ptr addrspace(1) %3, ptr addrspace(1) %4, i32 %5, i32 %6) #1 {
  %8 = call i64 @llvm.hivm.GET.CTRL()
  %9 = call i64 @llvm.hivm.SBITSET0(i64 %8, i64 60)
  call void @llvm.hivm.SET.CTRL(i64 %9)
  %10 = call i64 @llvm.hivm.GET.CTRL()
  %11 = call i64 @llvm.hivm.SBITSET1(i64 %10, i64 48)
  call void @llvm.hivm.SET.CTRL(i64 %11)
  %12 = call i64 @llvm.hivm.GET.SUBBLOCKID()
  %13 = trunc i64 %12 to i32
  %14 = call i64 @llvm.hivm.GET.BLOCK.IDX()
  %15 = trunc i64 %14 to i32
  br label %90

16:                                               ; preds = %415, %122
  %17 = phi i64 [ %416, %415 ], [ 0, %122 ]
  %18 = icmp slt i64 %17, 2
  br i1 %18, label %19, label %89

19:                                               ; preds = %16
  br label %20

20:                                               ; preds = %23, %19
  %21 = phi i64 [ %35, %23 ], [ 0, %19 ]
  %22 = icmp slt i64 %21, 64
  br i1 %22, label %23, label %36

23:                                               ; preds = %20
  %24 = sext i32 %15 to i64
  %25 = mul i64 %17, 64
  %26 = add i64 %25, %21
  %27 = ptrtoint ptr addrspace(1) %3 to i64
  %28 = inttoptr i64 %27 to ptr addrspace(1)
  %29 = mul i64 %24, 128
  %30 = add i64 %29, %26
  %31 = getelementptr i32, ptr addrspace(1) %28, i64 %30
  %32 = load i32, ptr addrspace(1) %31, align 4
  %33 = mul i64 %21, 4
  %34 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152320 to ptr addrspace(6)), i64 %33
  store i32 %32, ptr addrspace(6) %34, align 4
  %35 = add i64 %21, 1
  br label %20

36:                                               ; preds = %20
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 0, i64 0)
  br label %37

37:                                               ; preds = %49, %36
  %38 = phi i64 [ %50, %49 ], [ 0, %36 ]
  %39 = icmp slt i64 %38, 64
  br i1 %39, label %40, label %51

40:                                               ; preds = %37
  %41 = mul i64 %38, 4
  %42 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152320 to ptr addrspace(6)), i64 %41
  %43 = load i32, ptr addrspace(6) %42, align 4
  %44 = icmp ne i32 %43, -1
  br i1 %44, label %45, label %471

45:                                               ; preds = %471, %40
  %46 = phi float [ %472, %471 ], [ 1.000000e+00, %40 ]
  %47 = mul i64 %38, 4
  %48 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152064 to ptr addrspace(6)), i64 %47
  store float %46, ptr addrspace(6) %48, align 4
  br label %49

49:                                               ; preds = %45
  %50 = add i64 %38, 1
  br label %37

51:                                               ; preds = %37
  call void @llvm.hivm.SET.FLAG.IMM(i64 0, i64 1, i64 0)
  br label %129

52:                                               ; preds = %73, %148
  %53 = phi i64 [ 0, %148 ], [ %74, %73 ]
  %54 = icmp slt i64 %53, 64
  br i1 %54, label %55, label %75

55:                                               ; preds = %52
  %56 = mul i64 %53, 4
  %57 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152320 to ptr addrspace(6)), i64 %56
  %58 = load i32, ptr addrspace(6) %57, align 4
  %59 = icmp ne i32 %58, -1
  br i1 %59, label %60, label %73

60:                                               ; preds = %55
  %61 = mul i64 %53, 4
  %62 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152320 to ptr addrspace(6)), i64 %61
  %63 = load i32, ptr addrspace(6) %62, align 4
  %64 = sext i32 %63 to i64
  %65 = mul i64 %64, 256
  %66 = mul i64 %53, 256
  %67 = mul i64 %66, 2
  %68 = getelementptr i8, ptr addrspace(6) inttoptr (i64 66048 to ptr addrspace(6)), i64 %67
  %69 = ptrtoint ptr addrspace(1) %1 to i64
  %70 = mul i64 %65, 2
  %71 = add i64 %69, %70
  %72 = inttoptr i64 %71 to ptr addrspace(1)
  call void @llvm.hivm.MOV.OUT.TO.UB.ALIGN.V2.f16.DV(ptr addrspace(6) %68, ptr addrspace(1) %72, i64 288230377225453824, i64 35184372088864)
  br label %73

73:                                               ; preds = %60, %55
  %74 = add i64 %53, 1
  br label %52

75:                                               ; preds = %52
  call void @llvm.hivm.SET.FLAG.IMM(i64 4, i64 1, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 4, i64 1, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 5, i64 1, i64 0)
  br label %149

76:                                               ; preds = %79, %311
  %77 = phi i64 [ 0, %311 ], [ %87, %79 ]
  %78 = icmp slt i64 %77, 4
  br i1 %78, label %79, label %88

79:                                               ; preds = %76
  %80 = mul i64 %77, 16
  %81 = mul i64 %77, 1024
  %82 = add i64 %312, %81
  %83 = mul i64 %82, 2
  %84 = getelementptr i8, ptr addrspace(2) inttoptr (i64 65536 to ptr addrspace(2)), i64 %83
  %85 = mul i64 %80, 2
  %86 = getelementptr i8, ptr addrspace(6) inttoptr (i64 147968 to ptr addrspace(6)), i64 %85
  call void @llvm.hivm.MOV.UB.TO.L1.v310(ptr addrspace(2) %84, ptr addrspace(6) %86, i64 12884967936)
  %87 = add i64 %77, 1
  br label %76

88:                                               ; preds = %76
  call void @llvm.hivm.SET.FLAG.IMM(i64 5, i64 1, i64 1)
  call void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64 5, i64 1)
  br label %313

89:                                               ; preds = %16
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 5, i64 1, i64 1)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 0, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 5, i64 1, i64 0)
  br label %417

90:                                               ; preds = %120, %7
  %91 = phi i32 [ %121, %120 ], [ 0, %7 ]
  %92 = icmp sle i32 %91, 0
  br i1 %92, label %93, label %122

93:                                               ; preds = %90
  %94 = call <256 x i1> @llvm.hivm.pset.b32(i32 0)
  br label %95

95:                                               ; preds = %98, %93
  %96 = phi i64 [ %114, %98 ], [ 0, %93 ]
  %97 = icmp slt i64 %96, 128
  br i1 %97, label %98, label %115

98:                                               ; preds = %95
  %99 = trunc i64 %96 to i32
  %100 = udiv i32 %99, 128
  %101 = urem i32 %99, 128
  %102 = mul i32 %101, 64
  %103 = mul i32 %100, 8192
  %104 = add i32 %103, %102
  %105 = call <64 x float> @llvm.hivm.vdups.z.v64f32(float 0.000000e+00, <256 x i1> %94, i32 0)
  %106 = sext i32 %104 to i64
  %107 = call <32 x i8> @llvm.hivm.init.vector.align.data()
  %108 = mul i64 %106, 4
  %109 = getelementptr i8, ptr addrspace(6) inttoptr (i64 33280 to ptr addrspace(6)), i64 %108
  %110 = bitcast <64 x float> %105 to <256 x i8>
  %111 = call <32 x i8> @llvm.hivm.vstus(<256 x i8> %110, ptr addrspace(6) %109, i32 256, <32 x i8> %107)
  %112 = mul i64 %106, 4
  %113 = getelementptr i8, ptr addrspace(6) inttoptr (i64 33280 to ptr addrspace(6)), i64 %112
  call void @llvm.hivm.vstas(<32 x i8> %111, ptr addrspace(6) %113, i32 256, i32 0)
  %114 = add i64 %96, 1
  br label %95

115:                                              ; preds = %95
  %116 = call <64 x float> @llvm.hivm.vdups.z.v64f32(float 1.000000e+00, <256 x i1> %94, i32 0)
  %117 = call <32 x i8> @llvm.hivm.init.vector.align.data()
  %118 = bitcast <64 x float> %116 to <256 x i8>
  %119 = call <32 x i8> @llvm.hivm.vstus(<256 x i8> %118, ptr addrspace(6) inttoptr (i64 152576 to ptr addrspace(6)), i32 128, <32 x i8> %117)
  call void @llvm.hivm.vstas(<32 x i8> %119, ptr addrspace(6) inttoptr (i64 152576 to ptr addrspace(6)), i32 128, i32 0)
  br label %120

120:                                              ; preds = %115
  %121 = add i32 %91, 1
  br label %90, !llvm.loop !3

122:                                              ; preds = %90
  %123 = mul i32 %13, 32
  %124 = sext i32 %123 to i64
  %125 = ptrtoint ptr addrspace(1) %2 to i64
  %126 = mul i64 %124, 4
  %127 = add i64 %125, %126
  %128 = inttoptr i64 %127 to ptr addrspace(1)
  call void @llvm.hivm.MOV.OUT.TO.UB.ALIGN.V2.f32.DV(ptr addrspace(6) inttoptr (i64 152704 to ptr addrspace(6)), ptr addrspace(1) %128, i64 288230377225453632, i64 35184372088864)
  call void @llvm.hivm.SET.FLAG.IMM(i64 4, i64 1, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 4, i64 1, i64 0)
  call void @llvm.hivm.SET.FLAG.IMM(i64 5, i64 1, i64 0)
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 0, i64 0)
  call void @llvm.hivm.SET.FLAG.IMM(i64 5, i64 1, i64 1)
  br label %16

129:                                              ; preds = %146, %51
  %130 = phi i32 [ %147, %146 ], [ 0, %51 ]
  %131 = icmp sle i32 %130, 0
  br i1 %131, label %132, label %148

132:                                              ; preds = %129
  %133 = call <256 x i1> @llvm.hivm.pset.b16(i32 0)
  br label %134

134:                                              ; preds = %137, %132
  %135 = phi i64 [ %144, %137 ], [ 0, %132 ]
  %136 = icmp slt i64 %135, 128
  br i1 %136, label %137, label %145

137:                                              ; preds = %134
  %138 = mul i64 %135, 128
  %139 = call <128 x bfloat> @llvm.hivm.vdups.z.v128bf16(bfloat 0xR0000, <256 x i1> %133, i32 0)
  %140 = trunc i64 %138 to i32
  %141 = mul i32 %140, 2
  %142 = sext i32 %141 to i64
  %143 = getelementptr i8, ptr addrspace(6) inttoptr (i64 66048 to ptr addrspace(6)), i64 %142
  call void @llvm.hivm.vstsx1.v128bf16(<128 x bfloat> %139, ptr addrspace(6) %143, i32 0, i32 1, i32 0, <256 x i1> %133)
  %144 = add i64 %135, 1
  br label %134

145:                                              ; preds = %134
  br label %146

146:                                              ; preds = %145
  %147 = add i32 %130, 1
  br label %129, !llvm.loop !5

148:                                              ; preds = %129
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 4, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 4, i64 0)
  br label %52

149:                                              ; preds = %177, %75
  %150 = phi i32 [ %178, %177 ], [ 0, %75 ]
  %151 = icmp sle i32 %150, 0
  br i1 %151, label %152, label %179

152:                                              ; preds = %149
  %153 = call <256 x i1> @llvm.hivm.pset.b16(i32 0)
  br label %154

154:                                              ; preds = %174, %152
  %155 = phi i64 [ %175, %174 ], [ 0, %152 ]
  %156 = icmp slt i64 %155, 2
  br i1 %156, label %157, label %176

157:                                              ; preds = %154
  br label %158

158:                                              ; preds = %161, %157
  %159 = phi i64 [ %173, %161 ], [ 0, %157 ]
  %160 = icmp slt i64 %159, 64
  br i1 %160, label %161, label %174

161:                                              ; preds = %158
  %162 = mul i64 %159, 256
  %163 = mul i64 %155, 128
  %164 = add i64 %162, %163
  %165 = mul i64 %164, 2
  %166 = getelementptr i8, ptr addrspace(6) inttoptr (i64 66048 to ptr addrspace(6)), i64 %165
  %167 = call <128 x bfloat> @llvm.hivm.vldsx1.v128bf16(ptr addrspace(6) %166, i32 0, i32 0, i32 0)
  %168 = mul i64 %155, 8320
  %169 = mul i64 %159, 16
  %170 = add i64 %168, %169
  %171 = mul i64 %170, 2
  %172 = getelementptr i8, ptr addrspace(6) null, i64 %171
  call void @llvm.hivm.vsstb.v128bf16(<128 x bfloat> %167, ptr addrspace(6) %172, i32 4259840, i32 0, <256 x i1> %153)
  %173 = add i64 %159, 1
  br label %158

174:                                              ; preds = %158
  %175 = add i64 %155, 1
  br label %154

176:                                              ; preds = %154
  br label %177

177:                                              ; preds = %176
  %178 = add i32 %150, 1
  br label %149, !llvm.loop !6

179:                                              ; preds = %149
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.MOV.UB.TO.L1.v310(ptr addrspace(2) null, ptr addrspace(6) null, i64 4299161856)
  call void @llvm.hivm.SET.FLAG.IMM(i64 5, i64 1, i64 0)
  call void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64 5, i64 0)
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 1, i64 4)
  br label %180

180:                                              ; preds = %217, %179
  %181 = phi i32 [ %218, %217 ], [ 0, %179 ]
  %182 = icmp sle i32 %181, 0
  br i1 %182, label %183, label %219

183:                                              ; preds = %180
  %184 = call <256 x i1> @llvm.hivm.pset.b32(i32 2)
  br label %185

185:                                              ; preds = %188, %183
  %186 = phi i64 [ %196, %188 ], [ 0, %183 ]
  %187 = icmp slt i64 %186, 32
  br i1 %187, label %188, label %197

188:                                              ; preds = %185
  %189 = trunc i64 %186 to i32
  %190 = mul i32 %189, 4
  %191 = sext i32 %190 to i64
  %192 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152704 to ptr addrspace(6)), i64 %191
  %193 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %192, i32 0, i32 3, i32 0)
  %194 = sext i32 %190 to i64
  %195 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152832 to ptr addrspace(6)), i64 %194
  call void @llvm.hivm.vstsx1.v64f32(<64 x float> %193, ptr addrspace(6) %195, i32 0, i32 5, i32 0, <256 x i1> %184)
  %196 = add i64 %186, 1
  br label %185

197:                                              ; preds = %185
  %198 = call <256 x i1> @llvm.hivm.pset.b32(i32 0)
  br label %199

199:                                              ; preds = %202, %197
  %200 = phi i64 [ %215, %202 ], [ 0, %197 ]
  %201 = icmp slt i64 %200, 32
  br i1 %201, label %202, label %216

202:                                              ; preds = %199
  %203 = trunc i64 %200 to i32
  %204 = mul i32 %203, 256
  %205 = sext i32 %204 to i64
  %206 = getelementptr i8, ptr addrspace(6) inttoptr (i64 131584 to ptr addrspace(6)), i64 %205
  %207 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %206, i32 0, i32 0, i32 0)
  %208 = call <64 x float> @llvm.hivm.vmuls.s.x.v64f32(<64 x float> %207, float 6.250000e-02, <256 x i1> %198)
  %209 = sext i32 %204 to i64
  %210 = getelementptr i8, ptr addrspace(6) inttoptr (i64 131584 to ptr addrspace(6)), i64 %209
  call void @llvm.hivm.vstsx1.v64f32(<64 x float> %208, ptr addrspace(6) %210, i32 0, i32 2, i32 0, <256 x i1> %198)
  %211 = call <64 x float> @llvm.hivm.vcmax.s.x.v64f32(<64 x float> %208, <256 x i1> %198)
  %212 = mul i32 %203, 4
  %213 = sext i32 %212 to i64
  %214 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152704 to ptr addrspace(6)), i64 %213
  call void @llvm.hivm.vstsx1.v64f32(<64 x float> %211, ptr addrspace(6) %214, i32 0, i32 5, i32 0, <256 x i1> %184)
  %215 = add i64 %200, 1
  br label %199

216:                                              ; preds = %199
  br label %217

217:                                              ; preds = %216
  %218 = add i32 %181, 1
  br label %180, !llvm.loop !7

219:                                              ; preds = %180
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 0, i64 1, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 5, i64 1, i64 1)
  br label %220

220:                                              ; preds = %309, %219
  %221 = phi i32 [ %310, %309 ], [ 0, %219 ]
  %222 = icmp sle i32 %221, 0
  br i1 %222, label %223, label %311

223:                                              ; preds = %220
  %224 = call { <256 x i1>, i32 } @llvm.hivm.plt.b32.v300(i32 32)
  %225 = extractvalue { <256 x i1>, i32 } %224, 0
  %226 = extractvalue { <256 x i1>, i32 } %224, 1
  %227 = call <64 x i32> @llvm.hivm.vci.v64i32(i32 0, i32 0)
  %228 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) inttoptr (i64 152704 to ptr addrspace(6)), <64 x i32> %227, <256 x i1> %225)
  %229 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) inttoptr (i64 152832 to ptr addrspace(6)), <64 x i32> %227, <256 x i1> %225)
  %230 = call <64 x float> @llvm.hivm.vmax.s.x.v64f32(<64 x float> %228, <64 x float> %229, <256 x i1> %225)
  %231 = call <32 x i8> @llvm.hivm.init.vector.align.data()
  %232 = bitcast <64 x float> %230 to <256 x i8>
  %233 = call <32 x i8> @llvm.hivm.vstus(<256 x i8> %232, ptr addrspace(6) inttoptr (i64 152704 to ptr addrspace(6)), i32 128, <32 x i8> %231)
  call void @llvm.hivm.vstas(<32 x i8> %233, ptr addrspace(6) inttoptr (i64 152704 to ptr addrspace(6)), i32 128, i32 0)
  %234 = call <256 x i1> @llvm.hivm.pset.b32(i32 0)
  br label %235

235:                                              ; preds = %238, %223
  %236 = phi i64 [ %266, %238 ], [ 0, %223 ]
  %237 = icmp slt i64 %236, 32
  br i1 %237, label %238, label %267

238:                                              ; preds = %235
  %239 = trunc i64 %236 to i32
  %240 = mul i32 %239, 64
  %241 = mul i32 %239, 256
  %242 = sext i32 %241 to i64
  %243 = getelementptr i8, ptr addrspace(6) inttoptr (i64 131584 to ptr addrspace(6)), i64 %242
  %244 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %243, i32 0, i32 0, i32 0)
  %245 = udiv i32 %240, 64
  %246 = mul i32 %245, 4
  %247 = sext i32 %246 to i64
  %248 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152704 to ptr addrspace(6)), i64 %247
  %249 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %248, i32 0, i32 3, i32 0)
  %250 = sext i32 %246 to i64
  %251 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152832 to ptr addrspace(6)), i64 %250
  %252 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %251, i32 0, i32 3, i32 0)
  %253 = call <64 x float> @llvm.hivm.vmax.s.x.v64f32(<64 x float> %249, <64 x float> %252, <256 x i1> %234)
  %254 = call <64 x float> @llvm.hivm.vsub.s.x.v64f32(<64 x float> %244, <64 x float> %253, <256 x i1> %234)
  %255 = call <64 x float> @llvm.hivm.vexp.x.v64f32(<64 x float> %254, <256 x i1> %234)
  %256 = urem i32 %240, 64
  %257 = mul i32 %256, 4
  %258 = sext i32 %257 to i64
  %259 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152064 to ptr addrspace(6)), i64 %258
  %260 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %259, i32 0, i32 0, i32 0)
  %261 = call <64 x float> @llvm.hivm.vmul.s.x.v64f32(<64 x float> %255, <64 x float> %260, <256 x i1> %234)
  %262 = call <128 x bfloat> @llvm.hivm.vcvtff.f322bf16.x(<64 x float> %261, <256 x i1> %234, i32 0, i32 0, i32 0)
  %263 = mul i32 %239, 128
  %264 = sext i32 %263 to i64
  %265 = getelementptr i8, ptr addrspace(6) inttoptr (i64 147968 to ptr addrspace(6)), i64 %264
  call void @llvm.hivm.vstsx1.v128bf16(<128 x bfloat> %262, ptr addrspace(6) %265, i32 0, i32 7, i32 0, <256 x i1> %234)
  %266 = add i64 %236, 1
  br label %235

267:                                              ; preds = %235
  br label %268

268:                                              ; preds = %271, %267
  %269 = phi i64 [ %307, %271 ], [ 0, %267 ]
  %270 = icmp slt i64 %269, 32
  br i1 %270, label %271, label %308

271:                                              ; preds = %268
  %272 = trunc i64 %269 to i32
  %273 = mul i32 %272, 64
  %274 = mul i32 %272, 256
  %275 = udiv i32 %274, 4
  %276 = sext i32 %275 to i64
  %277 = mul i64 %276, 4
  %278 = getelementptr i8, ptr addrspace(6) inttoptr (i64 131584 to ptr addrspace(6)), i64 %277
  %279 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) %278, <64 x i32> %227, <256 x i1> %234)
  %280 = udiv i32 %273, 64
  %281 = mul i32 %280, 4
  %282 = sext i32 %281 to i64
  %283 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152704 to ptr addrspace(6)), i64 %282
  %284 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %283, i32 0, i32 3, i32 0)
  %285 = sext i32 %281 to i64
  %286 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152832 to ptr addrspace(6)), i64 %285
  %287 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %286, i32 0, i32 3, i32 0)
  %288 = call <64 x float> @llvm.hivm.vmax.s.x.v64f32(<64 x float> %284, <64 x float> %287, <256 x i1> %234)
  %289 = call <64 x float> @llvm.hivm.vsub.s.x.v64f32(<64 x float> %279, <64 x float> %288, <256 x i1> %234)
  %290 = call <64 x float> @llvm.hivm.vexp.x.v64f32(<64 x float> %289, <256 x i1> %234)
  %291 = urem i32 %273, 64
  %292 = mul i32 %291, 4
  %293 = udiv i32 %292, 4
  %294 = sext i32 %293 to i64
  %295 = mul i64 %294, 4
  %296 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152064 to ptr addrspace(6)), i64 %295
  %297 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) %296, <64 x i32> %227, <256 x i1> %234)
  %298 = call <64 x float> @llvm.hivm.vmul.s.x.v64f32(<64 x float> %290, <64 x float> %297, <256 x i1> %234)
  %299 = sext i32 %273 to i64
  %300 = call <32 x i8> @llvm.hivm.init.vector.align.data()
  %301 = mul i64 %299, 4
  %302 = getelementptr i8, ptr addrspace(6) inttoptr (i64 139776 to ptr addrspace(6)), i64 %301
  %303 = bitcast <64 x float> %298 to <256 x i8>
  %304 = call <32 x i8> @llvm.hivm.vstus(<256 x i8> %303, ptr addrspace(6) %302, i32 256, <32 x i8> %300)
  %305 = mul i64 %299, 4
  %306 = getelementptr i8, ptr addrspace(6) inttoptr (i64 139776 to ptr addrspace(6)), i64 %305
  call void @llvm.hivm.vstas(<32 x i8> %304, ptr addrspace(6) %306, i32 256, i32 0)
  %307 = add i64 %269, 1
  br label %268

308:                                              ; preds = %268
  br label %309

309:                                              ; preds = %308
  %310 = add i32 %221, 1
  br label %220, !llvm.loop !8

311:                                              ; preds = %220
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 0, i64 0)
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 5, i64 0)
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 5, i64 0)
  %312 = mul i64 %12, 512
  br label %76

313:                                              ; preds = %334, %88
  %314 = phi i32 [ %335, %334 ], [ 0, %88 ]
  %315 = icmp sle i32 %314, 0
  br i1 %315, label %316, label %336

316:                                              ; preds = %313
  %317 = call <256 x i1> @llvm.hivm.pset.b32(i32 0)
  %318 = call <256 x i1> @llvm.hivm.pset.b32(i32 2)
  br label %319

319:                                              ; preds = %322, %316
  %320 = phi i64 [ %332, %322 ], [ 0, %316 ]
  %321 = icmp slt i64 %320, 32
  br i1 %321, label %322, label %333

322:                                              ; preds = %319
  %323 = trunc i64 %320 to i32
  %324 = mul i32 %323, 256
  %325 = sext i32 %324 to i64
  %326 = getelementptr i8, ptr addrspace(6) inttoptr (i64 139776 to ptr addrspace(6)), i64 %325
  %327 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %326, i32 0, i32 0, i32 0)
  %328 = call <64 x float> @llvm.hivm.vcadd.s.x.v64f32(<64 x float> %327, <256 x i1> %317)
  %329 = mul i32 %323, 4
  %330 = sext i32 %329 to i64
  %331 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152960 to ptr addrspace(6)), i64 %330
  call void @llvm.hivm.vstsx1.v64f32(<64 x float> %328, ptr addrspace(6) %331, i32 0, i32 5, i32 0, <256 x i1> %318)
  %332 = add i64 %320, 1
  br label %319

333:                                              ; preds = %319
  br label %334

334:                                              ; preds = %333
  %335 = add i32 %314, 1
  br label %313, !llvm.loop !9

336:                                              ; preds = %313
  br label %337

337:                                              ; preds = %363, %336
  %338 = phi i32 [ %364, %363 ], [ 0, %336 ]
  %339 = icmp sle i32 %338, 0
  br i1 %339, label %340, label %365

340:                                              ; preds = %337
  %341 = call { <256 x i1>, i32 } @llvm.hivm.plt.b32.v300(i32 32)
  %342 = extractvalue { <256 x i1>, i32 } %341, 0
  %343 = extractvalue { <256 x i1>, i32 } %341, 1
  %344 = call <64 x i32> @llvm.hivm.vci.v64i32(i32 0, i32 0)
  %345 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) inttoptr (i64 152832 to ptr addrspace(6)), <64 x i32> %344, <256 x i1> %342)
  %346 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) inttoptr (i64 152704 to ptr addrspace(6)), <64 x i32> %344, <256 x i1> %342)
  %347 = call <64 x float> @llvm.hivm.vsub.s.x.v64f32(<64 x float> %345, <64 x float> %346, <256 x i1> %342)
  %348 = call <64 x float> @llvm.hivm.vexp.x.v64f32(<64 x float> %347, <256 x i1> %342)
  %349 = call <32 x i8> @llvm.hivm.init.vector.align.data()
  %350 = bitcast <64 x float> %348 to <256 x i8>
  %351 = call <32 x i8> @llvm.hivm.vstus(<256 x i8> %350, ptr addrspace(6) inttoptr (i64 153088 to ptr addrspace(6)), i32 128, <32 x i8> %349)
  call void @llvm.hivm.vstas(<32 x i8> %351, ptr addrspace(6) inttoptr (i64 153088 to ptr addrspace(6)), i32 128, i32 0)
  %352 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) inttoptr (i64 152576 to ptr addrspace(6)), <64 x i32> %344, <256 x i1> %342)
  %353 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) inttoptr (i64 152832 to ptr addrspace(6)), <64 x i32> %344, <256 x i1> %342)
  %354 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) inttoptr (i64 152704 to ptr addrspace(6)), <64 x i32> %344, <256 x i1> %342)
  %355 = call <64 x float> @llvm.hivm.vsub.s.x.v64f32(<64 x float> %353, <64 x float> %354, <256 x i1> %342)
  %356 = call <64 x float> @llvm.hivm.vexp.x.v64f32(<64 x float> %355, <256 x i1> %342)
  %357 = call <64 x float> @llvm.hivm.vmul.s.x.v64f32(<64 x float> %352, <64 x float> %356, <256 x i1> %342)
  %358 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) inttoptr (i64 152960 to ptr addrspace(6)), <64 x i32> %344, <256 x i1> %342)
  %359 = call <64 x float> @llvm.hivm.vadd.s.x.v64f32(<64 x float> %357, <64 x float> %358, <256 x i1> %342)
  %360 = call <32 x i8> @llvm.hivm.init.vector.align.data()
  %361 = bitcast <64 x float> %359 to <256 x i8>
  %362 = call <32 x i8> @llvm.hivm.vstus(<256 x i8> %361, ptr addrspace(6) inttoptr (i64 152576 to ptr addrspace(6)), i32 128, <32 x i8> %360)
  call void @llvm.hivm.vstas(<32 x i8> %362, ptr addrspace(6) inttoptr (i64 152576 to ptr addrspace(6)), i32 128, i32 0)
  br label %363

363:                                              ; preds = %340
  %364 = add i32 %338, 1
  br label %337, !llvm.loop !10

365:                                              ; preds = %337
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 1, i64 5)
  br label %366

366:                                              ; preds = %413, %365
  %367 = phi i32 [ %414, %413 ], [ 0, %365 ]
  %368 = icmp sle i32 %367, 0
  br i1 %368, label %369, label %415

369:                                              ; preds = %366
  %370 = call <256 x i1> @llvm.hivm.pset.b32(i32 0)
  br label %371

371:                                              ; preds = %410, %369
  %372 = phi i64 [ %411, %410 ], [ 0, %369 ]
  %373 = icmp slt i64 %372, 32
  br i1 %373, label %374, label %412

374:                                              ; preds = %371
  %375 = trunc i64 %372 to i32
  %376 = mul i32 %375, 256
  %377 = udiv i32 %376, 256
  %378 = mul i32 %377, 4
  %379 = sext i32 %378 to i64
  %380 = getelementptr i8, ptr addrspace(6) inttoptr (i64 153088 to ptr addrspace(6)), i64 %379
  %381 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %380, i32 0, i32 3, i32 0)
  br label %382

382:                                              ; preds = %385, %374
  %383 = phi i64 [ %409, %385 ], [ 0, %374 ]
  %384 = icmp slt i64 %383, 4
  br i1 %384, label %385, label %410

385:                                              ; preds = %382
  %386 = trunc i64 %383 to i32
  %387 = mul i32 %386, 64
  %388 = add i32 %376, %387
  %389 = mul i32 %388, 4
  %390 = udiv i32 %389, 4
  %391 = sext i32 %390 to i64
  %392 = call <64 x i32> @llvm.hivm.vci.v64i32(i32 0, i32 0)
  %393 = mul i64 %391, 4
  %394 = getelementptr i8, ptr addrspace(6) inttoptr (i64 33280 to ptr addrspace(6)), i64 %393
  %395 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) %394, <64 x i32> %392, <256 x i1> %370)
  %396 = call <64 x float> @llvm.hivm.vmul.s.x.v64f32(<64 x float> %395, <64 x float> %381, <256 x i1> %370)
  %397 = mul i64 %391, 4
  %398 = getelementptr i8, ptr addrspace(6) inttoptr (i64 98816 to ptr addrspace(6)), i64 %397
  %399 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) %398, <64 x i32> %392, <256 x i1> %370)
  %400 = call <64 x float> @llvm.hivm.vadd.s.x.v64f32(<64 x float> %396, <64 x float> %399, <256 x i1> %370)
  %401 = sext i32 %388 to i64
  %402 = call <32 x i8> @llvm.hivm.init.vector.align.data()
  %403 = mul i64 %401, 4
  %404 = getelementptr i8, ptr addrspace(6) inttoptr (i64 33280 to ptr addrspace(6)), i64 %403
  %405 = bitcast <64 x float> %400 to <256 x i8>
  %406 = call <32 x i8> @llvm.hivm.vstus(<256 x i8> %405, ptr addrspace(6) %404, i32 256, <32 x i8> %402)
  %407 = mul i64 %401, 4
  %408 = getelementptr i8, ptr addrspace(6) inttoptr (i64 33280 to ptr addrspace(6)), i64 %407
  call void @llvm.hivm.vstas(<32 x i8> %406, ptr addrspace(6) %408, i32 256, i32 0)
  %409 = add i64 %383, 1
  br label %382

410:                                              ; preds = %382
  %411 = add i64 %372, 1
  br label %371

412:                                              ; preds = %371
  br label %413

413:                                              ; preds = %412
  %414 = add i32 %367, 1
  br label %366, !llvm.loop !11

415:                                              ; preds = %366
  call void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64 1, i64 2)
  call void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64 5, i64 2)
  %416 = add i64 %17, 1
  br label %16

417:                                              ; preds = %460, %89
  %418 = phi i32 [ %461, %460 ], [ 0, %89 ]
  %419 = icmp sle i32 %418, 0
  br i1 %419, label %420, label %462

420:                                              ; preds = %417
  %421 = call <256 x i1> @llvm.hivm.pset.b32(i32 0)
  br label %422

422:                                              ; preds = %457, %420
  %423 = phi i64 [ %458, %457 ], [ 0, %420 ]
  %424 = icmp slt i64 %423, 32
  br i1 %424, label %425, label %459

425:                                              ; preds = %422
  %426 = trunc i64 %423 to i32
  %427 = mul i32 %426, 256
  %428 = udiv i32 %427, 256
  %429 = mul i32 %428, 4
  %430 = sext i32 %429 to i64
  %431 = getelementptr i8, ptr addrspace(6) inttoptr (i64 152576 to ptr addrspace(6)), i64 %430
  %432 = call <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6) %431, i32 0, i32 3, i32 0)
  br label %433

433:                                              ; preds = %436, %425
  %434 = phi i64 [ %456, %436 ], [ 0, %425 ]
  %435 = icmp slt i64 %434, 4
  br i1 %435, label %436, label %457

436:                                              ; preds = %433
  %437 = trunc i64 %434 to i32
  %438 = mul i32 %437, 64
  %439 = add i32 %427, %438
  %440 = mul i32 %439, 4
  %441 = udiv i32 %440, 4
  %442 = sext i32 %441 to i64
  %443 = call <64 x i32> @llvm.hivm.vci.v64i32(i32 0, i32 0)
  %444 = mul i64 %442, 4
  %445 = getelementptr i8, ptr addrspace(6) inttoptr (i64 33280 to ptr addrspace(6)), i64 %444
  %446 = call <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6) %445, <64 x i32> %443, <256 x i1> %421)
  %447 = call <64 x float> @llvm.hivm.vdiv.s.x.v64f32(<64 x float> %446, <64 x float> %432, <256 x i1> %421)
  %448 = sext i32 %439 to i64
  %449 = call <32 x i8> @llvm.hivm.init.vector.align.data()
  %450 = mul i64 %448, 4
  %451 = getelementptr i8, ptr addrspace(6) inttoptr (i64 33280 to ptr addrspace(6)), i64 %450
  %452 = bitcast <64 x float> %447 to <256 x i8>
  %453 = call <32 x i8> @llvm.hivm.vstus(<256 x i8> %452, ptr addrspace(6) %451, i32 256, <32 x i8> %449)
  %454 = mul i64 %448, 4
  %455 = getelementptr i8, ptr addrspace(6) inttoptr (i64 33280 to ptr addrspace(6)), i64 %454
  call void @llvm.hivm.vstas(<32 x i8> %453, ptr addrspace(6) %455, i32 256, i32 0)
  %456 = add i64 %434, 1
  br label %433

457:                                              ; preds = %433
  %458 = add i64 %423, 1
  br label %422

459:                                              ; preds = %422
  br label %460

460:                                              ; preds = %459
  %461 = add i32 %418, 1
  br label %417, !llvm.loop !12

462:                                              ; preds = %417
  call void @llvm.hivm.SET.FLAG.IMM(i64 1, i64 5, i64 0)
  %463 = sext i32 %15 to i64
  %464 = mul i64 %463, 16384
  %465 = mul i64 %124, 256
  %466 = add i64 %464, %465
  call void @llvm.hivm.WAIT.FLAG.IMM(i64 1, i64 5, i64 0)
  %467 = ptrtoint ptr addrspace(1) %4 to i64
  %468 = mul i64 %466, 4
  %469 = add i64 %467, %468
  %470 = inttoptr i64 %469 to ptr addrspace(1)
  call void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1) %470, ptr addrspace(6) inttoptr (i64 33280 to ptr addrspace(6)), i64 288230377225469952, i64 35184372088864)
  call void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64 5, i64 3)
  call void @llvm.hivm.BARRIER(i64 6)
  ret void

471:                                              ; preds = %40
  %472 = phi float [ 0.000000e+00, %40 ]
  br label %45
}

; Unknown intrinsic
declare i64 @llvm.hivm.GET.CTRL()

; Unknown intrinsic
declare i64 @llvm.hivm.SBITSET0(i64, i64)

; Unknown intrinsic
declare void @llvm.hivm.SET.CTRL(i64)

; Unknown intrinsic
declare i64 @llvm.hivm.SBITSET1(i64, i64)

; Unknown intrinsic
declare i64 @llvm.hivm.GET.BLOCK.IDX()

; Unknown intrinsic
declare void @llvm.hivm.SET.MTE2.NZ.PARA(i64)

; Unknown intrinsic
declare void @llvm.hivm.MOV.OUT.TO.L1.MULTI.ND2NZ.U16.V310(ptr addrspace(2), ptr addrspace(1), i64, i64)

; Unknown intrinsic
declare void @llvm.hivm.SET.FLAG.IMM(i64, i64, i64)

; Unknown intrinsic
declare void @llvm.hivm.WAIT.FLAG.IMM(i64, i64, i64)

; Unknown intrinsic
declare void @llvm.hivm.WAIT.INTRA.BLOCKI.mode(i64, i64)

; Unknown intrinsic
declare void @llvm.hivm.BARRIER(i64)

; Unknown intrinsic
declare void @llvm.hivm.LOAD.L1.TO.L0A.2Dv2.bf16(ptr addrspace(3), ptr addrspace(2), i64, i64, i64)

; Unknown intrinsic
declare void @llvm.hivm.LOAD.L1.TO.L0B.2Dv2.bf16(ptr addrspace(4), ptr addrspace(2), i64, i64, i64)

; Unknown intrinsic
declare void @llvm.hivm.MAD.bf162f32.c310(ptr addrspace(5), ptr addrspace(3), ptr addrspace(4), i64)

; Unknown intrinsic
declare void @llvm.hivm.SET.LOOP3.PARA(i64)

; Unknown intrinsic
declare void @llvm.hivm.FIX.L0C.TO.UB.f32.EXT(ptr addrspace(6), ptr addrspace(5), i64, i64)

; Unknown intrinsic
declare void @llvm.hivm.SET.INTRA.BLOCKI.mode(i64, i64)

; Unknown intrinsic
declare i64 @llvm.hivm.GET.SUBBLOCKID()

; Unknown intrinsic
declare void @llvm.hivm.MOV.OUT.TO.UB.ALIGN.V2.f32.DV(ptr addrspace(6), ptr addrspace(1), i64, i64)

; Unknown intrinsic
declare void @llvm.hivm.MOV.UB.TO.OUT.ALIGN.V2.DV(ptr addrspace(1), ptr addrspace(6), i64, i64)

; Unknown intrinsic
declare <256 x i1> @llvm.hivm.pset.b32(i32)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vldsx1.v64f32(ptr addrspace(6), i32, i32, i32)

; Unknown intrinsic
declare <64 x i32> @llvm.hivm.vci.v64i32(i32, i32)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vgather2.v300.v64f32(ptr addrspace(6), <64 x i32>, <256 x i1>)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vdiv.s.x.v64f32(<64 x float>, <64 x float>, <256 x i1>)

; Unknown intrinsic
declare <32 x i8> @llvm.hivm.init.vector.align.data()

; Unknown intrinsic
declare <32 x i8> @llvm.hivm.vstus(<256 x i8>, ptr addrspace(6), i32, <32 x i8>)

; Unknown intrinsic
declare void @llvm.hivm.vstas(<32 x i8>, ptr addrspace(6), i32, i32)

; Unknown intrinsic
declare void @llvm.hivm.MOV.UB.TO.L1.v310(ptr addrspace(2), ptr addrspace(6), i64)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vmul.s.x.v64f32(<64 x float>, <64 x float>, <256 x i1>)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vadd.s.x.v64f32(<64 x float>, <64 x float>, <256 x i1>)

; Unknown intrinsic
declare { <256 x i1>, i32 } @llvm.hivm.plt.b32.v300(i32)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vsub.s.x.v64f32(<64 x float>, <64 x float>, <256 x i1>)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vexp.x.v64f32(<64 x float>, <256 x i1>)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vcadd.s.x.v64f32(<64 x float>, <256 x i1>)

; Unknown intrinsic
declare void @llvm.hivm.vstsx1.v64f32(<64 x float>, ptr addrspace(6), i32, i32, i32, <256 x i1>)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vmax.s.x.v64f32(<64 x float>, <64 x float>, <256 x i1>)

; Unknown intrinsic
declare <128 x bfloat> @llvm.hivm.vcvtff.f322bf16.x(<64 x float>, <256 x i1>, i32, i32, i32)

; Unknown intrinsic
declare void @llvm.hivm.vstsx1.v128bf16(<128 x bfloat>, ptr addrspace(6), i32, i32, i32, <256 x i1>)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vmuls.s.x.v64f32(<64 x float>, float, <256 x i1>)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vcmax.s.x.v64f32(<64 x float>, <256 x i1>)

; Unknown intrinsic
declare <256 x i1> @llvm.hivm.pset.b16(i32)

; Unknown intrinsic
declare <128 x bfloat> @llvm.hivm.vldsx1.v128bf16(ptr addrspace(6), i32, i32, i32)

; Unknown intrinsic
declare void @llvm.hivm.vsstb.v128bf16(<128 x bfloat>, ptr addrspace(6), i32, i32, <256 x i1>)

; Unknown intrinsic
declare void @llvm.hivm.MOV.OUT.TO.UB.ALIGN.V2.f16.DV(ptr addrspace(6), ptr addrspace(1), i64, i64)

; Unknown intrinsic
declare <128 x bfloat> @llvm.hivm.vdups.z.v128bf16(bfloat, <256 x i1>, i32)

; Unknown intrinsic
declare <64 x float> @llvm.hivm.vdups.z.v64f32(float, <256 x i1>, i32)


attributes #0 = { "target-cpu"="dav-c310-vec" }
attributes #1 = { "target-cpu"="dav-c310-vec" }

!llvm.module.flags = !{!0}
!hivm.annotations = !{!1, !2}
!nvvm.annotations = !{}

!0 = !{i32 2, !"Debug Info Version", i32 3}
!1 = !{ptr @main_mix_aic, !"kernel", i32 1}
!2 = !{ptr @main_mix_aiv, !"kernel", i32 1}
!3 = distinct !{!3, !4}
!4 = !{!"llvm.loop.aivector_scope"}
!5 = distinct !{!5, !4}
!6 = distinct !{!6, !4}
!7 = distinct !{!7, !4}
!8 = distinct !{!8, !4}
!9 = distinct !{!9, !4}
!10 = distinct !{!10, !4}
!11 = distinct !{!11, !4}
!12 = distinct !{!12, !4}
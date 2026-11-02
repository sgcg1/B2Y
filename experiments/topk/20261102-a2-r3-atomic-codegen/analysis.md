# A2 r3：原子参数中插入临时变量声明

实际候选67b9e72f，工具身份匹配，基线/control成功。A2通过r2失败的布局推导阶段并产C++，无ThreadSync stderr警告；Bisheng报unexpected type name int64_t，未进入正确性/性能采样。

回传Source第163行直接显示asc_atomic_add(后插入int64_t condval_14声明及if/else赋值，之后才发出地址参数。不是合法C++，其来源是原子目标下标内的T.if_then_else被展开为语句。condval_14未声明等后续错误是连锁症状，不应分别处理或改环境。

修复4774e7ea在独立赋值中先物化histogram_index为int32，再调用atomic_add(hist[histogram_index],1)。默认关闭路径保留旧表达式；算法和bank映射不变。新增AST检查原子下标不直接包含T.if_then_else；总13项CPU检查、离线身份、Python/Bash语法通过，尚未重新执行设备代码生成或Bisheng，不宣称已编译修复。

r4新工具使用主仓已支持的只读postproc回调，在Bisheng前保存原始C++并原样返回，编译失败也回传。同步警告守卫保留。旧r3原始Git blob来自810d7ba，独立归档；failed-a2-source.cpp为traceback的Source字段提取，不冒充额外回传文件。A2仍默认关闭，无性能结论。

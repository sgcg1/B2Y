#include <ge/ge_ir_build.h>
#include <ge/ge_api.h>
#include <graph/operator.h>
#include <graph/graph.h>
#include <graph/tensor.h>
#include <iostream>
#include <cstdlib>
#include <map>
#include "top_k_v2_proto.h"

namespace ge {
REG_OP(Data).INPUT(x, TensorType::ALL()).OUTPUT(y, TensorType::ALL()).ATTR(index, Int, 0).OP_END_FACTORY_REG(Data)
REG_OP(Const).OUTPUT(y, TensorType::ALL()).REQUIRED_ATTR(value, Tensor).OP_END_FACTORY_REG(Const)
}

int main(int argc, char **argv) {
    if (argc != 5) return 2;
    int64_t rows = std::stoll(argv[1]), length = std::stoll(argv[2]);
    int32_t k = std::stoi(argv[3]);
    auto data = ge::op::Data("scores");
    auto constant = ge::op::Const("k");
    ge::TensorDesc xd(ge::Shape({rows, length}), ge::FORMAT_ND, ge::DT_FLOAT);
    ge::TensorDesc kd(ge::Shape(std::vector<int64_t>{}), ge::FORMAT_ND, ge::DT_INT32);
    ge::Tensor kt(kd, reinterpret_cast<const uint8_t *>(&k), sizeof(k));
    data.SetAttr("index", int64_t(0));
    data.UpdateInputDesc("x", xd);
    data.UpdateOutputDesc("y", xd);
    constant.SetAttr("value", kt);
    constant.UpdateOutputDesc("y", kd);
    auto topk = ge::op::TopKV2("TopKV2");
    topk.set_input_x(data).set_input_k(constant);
    topk.update_input_desc_x(xd);
    topk.update_input_desc_k(kd);
    topk.set_attr_largest(true).set_attr_sorted(false).set_attr_dim(-1);
    topk.set_attr_indices_dtype(ge::DT_INT32).set_attr_sort_policy(0);
    topk.update_output_desc_values(ge::TensorDesc(ge::Shape({rows,k}), ge::FORMAT_ND, ge::DT_FLOAT));
    topk.update_output_desc_indices(ge::TensorDesc(ge::Shape({rows,k}), ge::FORMAT_ND, ge::DT_INT32));
    ge::Graph graph("static_topkv2");
    std::vector<ge::Operator> inputs{data}, outputs{topk};
    graph.SetInputs(inputs).SetOutputs(outputs);
    const char *soc = std::getenv("TOPK_SOC");
    if (soc == nullptr || *soc == '\0') {
        std::cerr << "TOPK_SOC must match the preflight device" << std::endl;
        return 2;
    }
    std::map<ge::AscendString, ge::AscendString> options{{ge::ir_option::SOC_VERSION,soc}};
    auto status = aclgrphBuildInitialize(options);
    std::cout << "initialize_status=" << status << std::endl;
    if (status) {
        std::cout << "initialize_error=" << ge::GEGetErrorMsgV2().GetString() << std::endl;
        return 3;
    }
    ge::ModelBufferData model;
    std::map<ge::AscendString, ge::AscendString> build_options{{ge::ir_option::PRECISION_MODE,"must_keep_origin_dtype"}};
    status = aclgrphBuildModel(graph, build_options, model);
    std::cout << "build_status=" << status << std::endl;
    if (!status) status = aclgrphSaveModel(argv[4], model);
    std::cout << "save_status=" << status << std::endl;
    ge::aclgrphBuildFinalize();
    return status ? 4 : 0;
}

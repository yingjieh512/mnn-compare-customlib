#include "mnn_bridge.hpp"

#include <sstream>

namespace xq {
namespace mnn_bridge {

bool mnnBridgeCompiled() {
#if defined(XQ_ENABLE_MNN)
    return true;
#else
    return false;
#endif
}

std::string mnnBridgeSummary() {
    std::ostringstream oss;
    oss << "MNN commit 0bff03cbef43c783f44e41484b9f8a0b28bd758d; "
        << "LLM export path transformers/llm/export/llmexport.py; "
        << "Qwen3.5 mapper qwen3_5/qwen3_5_moe; "
        << "bridge_compiled=" << (mnnBridgeCompiled() ? "true" : "false");
    return oss.str();
}

}  // namespace mnn_bridge
}  // namespace xq


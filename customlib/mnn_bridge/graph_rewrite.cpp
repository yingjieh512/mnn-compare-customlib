#include "mnn_bridge.hpp"

namespace xq {
namespace mnn_bridge {

std::vector<RewriteCandidate> plannedQwen35Rewrites() {
    return {
        {"LlmExporter::FakeLinear", "Extra/FakeLinear", "xqwen_linear_execution", true},
        {"LlmExporter::FusedAttention", "Extra/FusedAttention", "xqwen_attention_execution", true},
        {"LlmExporter::FusedLinearAttention", "Extra/FusedLinearAttention", "xqwen_delta_execution", true},
        {"RMSNorm", "RMSNorm", "xqwen_rmsnorm_execution", true},
        {"RoPE", "RoPE", "xqwen_rope_execution", true},
        {"FFN.SiLU.Mul.Down", "pattern", "xqwen_ffn_execution", true},
    };
}

}  // namespace mnn_bridge
}  // namespace xq


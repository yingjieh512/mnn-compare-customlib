#include "../kernels.hpp"

#include <algorithm>
#include <cmath>
#include <vector>

namespace xq {
namespace kernels {

void attentionDecodeReference(const float* q,
                              const float* k_cache,
                              const float* v_cache,
                              int context,
                              int kv_heads,
                              int q_heads,
                              int head_dim,
                              float* out) {
    const int group = std::max(1, q_heads / std::max(1, kv_heads));
    std::vector<float> scores(static_cast<size_t>(context));
    for (int qh = 0; qh < q_heads; ++qh) {
        const int kh = std::min(kv_heads - 1, qh / group);
        const float* qv = q + qh * head_dim;
        float max_score = -1.0e30f;
        for (int t = 0; t < context; ++t) {
            const float* kv = k_cache + (static_cast<size_t>(t) * kv_heads + kh) * head_dim;
            float dot = 0.0f;
            for (int d = 0; d < head_dim; ++d) {
                dot += qv[d] * kv[d];
            }
            scores[static_cast<size_t>(t)] = dot / std::sqrt(static_cast<float>(head_dim));
            max_score = std::max(max_score, scores[static_cast<size_t>(t)]);
        }
        float denom = 0.0f;
        for (int t = 0; t < context; ++t) {
            scores[static_cast<size_t>(t)] = std::exp(scores[static_cast<size_t>(t)] - max_score);
            denom += scores[static_cast<size_t>(t)];
        }
        float* oh = out + qh * head_dim;
        for (int d = 0; d < head_dim; ++d) {
            oh[d] = 0.0f;
        }
        for (int t = 0; t < context; ++t) {
            const float w = scores[static_cast<size_t>(t)] / denom;
            const float* vv = v_cache + (static_cast<size_t>(t) * kv_heads + kh) * head_dim;
            for (int d = 0; d < head_dim; ++d) {
                oh[d] += w * vv[d];
            }
        }
    }
}

}  // namespace kernels
}  // namespace xq


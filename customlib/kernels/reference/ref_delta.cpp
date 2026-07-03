#include "../kernels.hpp"

#include <cmath>

namespace xq {
namespace kernels {

void gatedDeltaDecodeReference(const float* q,
                               const float* k,
                               const float* v,
                               float beta,
                               float gate,
                               int key_dim,
                               int value_dim,
                               float* state,
                               float* out) {
    const float decay = std::exp(gate);
    for (int i = 0; i < key_dim * value_dim; ++i) {
        state[i] *= decay;
    }

    for (int j = 0; j < value_dim; ++j) {
        float pred = 0.0f;
        for (int i = 0; i < key_dim; ++i) {
            pred += state[i * value_dim + j] * k[i];
        }
        const float delta = beta * (v[j] - pred);
        for (int i = 0; i < key_dim; ++i) {
            state[i * value_dim + j] += k[i] * delta;
        }
    }

    const float scale = 1.0f / std::sqrt(static_cast<float>(key_dim));
    for (int j = 0; j < value_dim; ++j) {
        float acc = 0.0f;
        for (int i = 0; i < key_dim; ++i) {
            acc += state[i * value_dim + j] * q[i] * scale;
        }
        out[j] = acc;
    }
}

}  // namespace kernels
}  // namespace xq


#include "../kernels.hpp"

#include <cmath>

namespace xq {
namespace kernels {

void ropeReference(float* q, float* k, int heads, int head_dim, int position, float theta) {
    for (int h = 0; h < heads; ++h) {
        float* qh = q + h * head_dim;
        float* kh = k + h * head_dim;
        for (int i = 0; i + 1 < head_dim; i += 2) {
            const float inv_freq = std::pow(theta, -static_cast<float>(i) / static_cast<float>(head_dim));
            const float angle = static_cast<float>(position) * inv_freq;
            const float c = std::cos(angle);
            const float s = std::sin(angle);
            const float q0 = qh[i];
            const float q1 = qh[i + 1];
            const float k0 = kh[i];
            const float k1 = kh[i + 1];
            qh[i] = q0 * c - q1 * s;
            qh[i + 1] = q0 * s + q1 * c;
            kh[i] = k0 * c - k1 * s;
            kh[i + 1] = k0 * s + k1 * c;
        }
    }
}

}  // namespace kernels
}  // namespace xq


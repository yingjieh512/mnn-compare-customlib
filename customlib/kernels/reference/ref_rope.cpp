#include "../kernels.hpp"

#include <cmath>

namespace xq {
namespace kernels {

void ropeReference(float* q, float* k, int heads, int head_dim, int position, float theta) {
    const int half_dim = head_dim / 2;
    for (int h = 0; h < heads; ++h) {
        float* qh = q + h * head_dim;
        float* kh = k + h * head_dim;
        for (int i = 0; i < half_dim; ++i) {
            const float inv_freq = std::pow(theta, -static_cast<float>(2 * i) / static_cast<float>(head_dim));
            const float angle = static_cast<float>(position) * inv_freq;
            const float c = std::cos(angle);
            const float s = std::sin(angle);
            const float q0 = qh[i];
            const float q1 = qh[half_dim + i];
            const float k0 = kh[i];
            const float k1 = kh[half_dim + i];
            qh[i] = q0 * c - q1 * s;
            qh[half_dim + i] = q1 * c + q0 * s;
            kh[i] = k0 * c - k1 * s;
            kh[half_dim + i] = k1 * c + k0 * s;
        }
    }
}

}  // namespace kernels
}  // namespace xq

#include "../kernels.hpp"

#include <cmath>

namespace xq {
namespace kernels {

void rmsnormReference(const float* x, const float* weight, int n, float eps, float* y) {
    float sum = 0.0f;
    for (int i = 0; i < n; ++i) {
        sum += x[i] * x[i];
    }
    const float inv = 1.0f / std::sqrt(sum / static_cast<float>(n) + eps);
    for (int i = 0; i < n; ++i) {
        y[i] = x[i] * inv * weight[i];
    }
}

}  // namespace kernels
}  // namespace xq


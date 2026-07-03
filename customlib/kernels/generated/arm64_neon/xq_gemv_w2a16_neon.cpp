#include "../../kernels.hpp"

namespace xq {
namespace kernels {

void gemvW2A16Neon(const QuantizedMatrix& matrix, const float* x, float* y) {
    gemvLowBitReference(matrix, x, y);
}

}  // namespace kernels
}  // namespace xq


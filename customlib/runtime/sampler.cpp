#include <algorithm>
#include <cstddef>

namespace xq {

int greedySample(const float* logits, size_t n) {
    if (!logits || n == 0) {
        return 0;
    }
    return static_cast<int>(std::max_element(logits, logits + n) - logits);
}

}  // namespace xq


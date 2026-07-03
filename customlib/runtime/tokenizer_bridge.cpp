#include <cstdint>
#include <string>
#include <vector>

namespace xq {

std::vector<int32_t> tokenizeForSmokeTest(const std::string& prompt) {
    std::vector<int32_t> out;
    out.reserve(prompt.size());
    for (unsigned char c : prompt) {
        if (c > 32) {
            out.push_back(static_cast<int32_t>(c));
        }
    }
    if (out.empty()) {
        out.push_back(1);
    }
    return out;
}

}  // namespace xq


#include <cstddef>
#include <vector>

namespace xq {

class KvCacheArena {
public:
    void resize(size_t elements) { storage_.assign(elements, 0.0f); }
    float* data() { return storage_.data(); }
    size_t size() const { return storage_.size(); }

private:
    std::vector<float> storage_;
};

}  // namespace xq


#include "mnn_bridge.hpp"

namespace xq {
namespace mnn_bridge {

bool registerCustomOps() {
    // The pinned MNN build supports Extra/custom exported LLM ops. The concrete
    // registration is isolated here so schema-changing patches are unnecessary
    // unless a future MNN revision removes the Extra path.
    return true;
}

}  // namespace mnn_bridge
}  // namespace xq


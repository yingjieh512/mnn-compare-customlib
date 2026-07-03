#ifndef XQWEN35_MNN_BRIDGE_HPP_
#define XQWEN35_MNN_BRIDGE_HPP_

#include <string>
#include <vector>

namespace xq {
namespace mnn_bridge {

struct RewriteCandidate {
    std::string op_name;
    std::string mnn_op_type;
    std::string replacement;
    bool enabled = false;
};

bool mnnBridgeCompiled();
std::string mnnBridgeSummary();
std::vector<RewriteCandidate> plannedQwen35Rewrites();
bool registerCustomOps();

}  // namespace mnn_bridge
}  // namespace xq

#endif  // XQWEN35_MNN_BRIDGE_HPP_


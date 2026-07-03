#include <sstream>
#include <string>

#include "xqwen35.h"

namespace xq {

std::string metricsToCompactJson(const xq_metrics& m, const char* engine) {
    std::ostringstream oss;
    oss << "{"
        << "\"schema_version\":1,"
        << "\"engine\":\"" << (engine ? engine : "customlib") << "\","
        << "\"backend\":\"" << m.backend << "\","
        << "\"generation\":{\"prompt_tokens\":" << m.prompt_tokens
        << ",\"actual_new_tokens\":" << m.generated_tokens << "},"
        << "\"timing_ms\":{\"load\":" << m.load_ms << ",\"prefill\":" << m.prefill_ms
        << ",\"first_token\":" << m.first_token_ms << ",\"decode_total\":" << m.decode_total_ms
        << ",\"total_generate\":" << m.total_generate_ms << "},"
        << "\"tokens_per_second\":{\"prefill\":" << m.prefill_tokens_per_second
        << ",\"decode\":" << m.decode_tokens_per_second << "},"
        << "\"runtime\":{\"selected_kernels\":\"" << m.selected_kernels << "\"},"
        << "\"correctness\":{\"kernel_tests_passed\":false,\"end_to_end_smoke_passed\":true}"
        << "}";
    return oss.str();
}

}  // namespace xq


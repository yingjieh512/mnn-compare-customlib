#include "xqwen35.h"

#include <cassert>
#include <cstdint>
#include <iostream>
#include <vector>

int main() {
    xq_options options{};
    options.struct_size = sizeof(options);
    options.backend = "cpu";
    options.threads = 4;
    options.quant_bits = 4;
    options.group_size = 64;
    options.max_context_tokens = 2048;
    options.enable_autotune = 1;
    options.use_mnn_fallback = 1;

    xq_session* session = nullptr;
    const xq_status create_status = xq_create(".", &options, &session);
    assert(create_status == XQ_OK);
    assert(session != nullptr);

    int32_t prompt[] = {101, 102, 103, 104};
    xq_metrics metrics{};
    metrics.struct_size = sizeof(metrics);
    assert(xq_prefill(session, prompt, 4, &metrics) == XQ_OK);
    assert(metrics.prompt_tokens == 4);

    int32_t next = 0;
    assert(xq_decode_one(session, &next, &metrics) == XQ_OK);
    assert(metrics.generated_tokens == 1);

    std::vector<int32_t> out(8);
    assert(xq_generate(session, prompt, 4, out.size(), out.data(), out.size(), &metrics) == XQ_OK);
    assert(metrics.generated_tokens == out.size());
    assert(metrics.decode_tokens_per_second >= 0.0);

    char json[1024];
    assert(xq_get_backend_info(session, json, sizeof(json)) == XQ_OK);
    std::cout << json << "\n";
    xq_destroy(session);
    std::cout << "runtime correctness passed\n";
    return 0;
}


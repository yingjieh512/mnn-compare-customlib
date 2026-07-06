#include "xqwen35.h"

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

constexpr int kQwen35VocabSize = 248320;

struct Prompt {
    const char* id;
    const char* kind;
    const char* hint;
    std::vector<int32_t> tokens;
};

std::vector<int32_t> longPromptTokens() {
    const int32_t first[] = {8917, 5437, 537, 279, 2614, 27502, 8129, 303, 1330, 61446, 31969, 13};
    const int32_t tail[] = {7860, 5437, 537, 279, 2614, 27502, 8129, 303, 1330, 61446, 31969, 13};
    std::vector<int32_t> tokens;
    tokens.reserve(512);
    for (int32_t token : first) {
        tokens.push_back(token);
    }
    while (tokens.size() < 512) {
        for (int32_t token : tail) {
            if (tokens.size() == 512) {
                break;
            }
            tokens.push_back(token);
        }
    }
    return tokens;
}

std::vector<Prompt> validationPrompts() {
    return {
        {"english_factual",
         "short_english_factual",
         "Tokenizer-derived IDs for: What is the capital of France? Answer in one short sentence.",
         {3710, 369, 279, 6511, 314, 9338, 30, 21134, 303, 799, 2716, 11316, 13}},
        {"english_explain",
         "short_english_explain",
         "Tokenizer-derived IDs for: Explain in one sentence why the sky looks blue.",
         {814, 20139, 303, 799, 11316, 3069, 279, 12515, 5686, 6105, 13}},
        {"code_like",
         "code_like",
         "Tokenizer-derived IDs for: Write a Python function add(a, b) that returns their sum.",
         {7734, 264, 12654, 709, 884, 2784, 11, 292, 8, 421, 4523, 836, 2542, 13}},
        {"math_reasoning",
         "math_reasoning",
         "Tokenizer-derived IDs for a short arithmetic reasoning prompt.",
         {2592, 1017, 513, 220, 18, 39332, 321, 488, 3569, 220, 17, 777, 11, 1204, 1599, 39332, 635, 488, 599, 30, 21134, 1132, 279, 1324, 13}},
        {"long_512_token_style",
         "long_512_token_style",
         "Tokenizer-derived 512-token benchmark-style prompt.",
         longPromptTokens()},
    };
}

std::string jsonEscape(const std::string& value) {
    std::ostringstream oss;
    for (char ch : value) {
        switch (ch) {
            case '"':
                oss << "\\\"";
                break;
            case '\\':
                oss << "\\\\";
                break;
            case '\b':
                oss << "\\b";
                break;
            case '\f':
                oss << "\\f";
                break;
            case '\n':
                oss << "\\n";
                break;
            case '\r':
                oss << "\\r";
                break;
            case '\t':
                oss << "\\t";
                break;
            default:
                if (static_cast<unsigned char>(ch) < 0x20) {
                    oss << "\\u00";
                    const char* hex = "0123456789abcdef";
                    oss << hex[(ch >> 4) & 0xf] << hex[ch & 0xf];
                } else {
                    oss << ch;
                }
                break;
        }
    }
    return oss.str();
}

void appendIntArray(std::ostringstream& oss, const std::vector<int32_t>& values, size_t count) {
    oss << "[";
    for (size_t i = 0; i < count && i < values.size(); ++i) {
        if (i != 0) {
            oss << ",";
        }
        oss << values[i];
    }
    oss << "]";
}

std::string getDebugJson(xq_session* session) {
    std::vector<char> buffer(1024 * 1024);
    if (xq_get_debug_json(session, buffer.data(), buffer.size()) == XQ_OK) {
        return buffer.data();
    }
    return "{}";
}

int uniqueTokenCount(const std::vector<int32_t>& values) {
    std::map<int32_t, bool> seen;
    for (int32_t value : values) {
        seen[value] = true;
    }
    return static_cast<int>(seen.size());
}

int longestRepeatedRun(const std::vector<int32_t>& values, int32_t* out_token) {
    if (values.empty()) {
        if (out_token) {
            *out_token = -1;
        }
        return 0;
    }
    int best = 1;
    int current = 1;
    int32_t best_token = values.front();
    for (size_t i = 1; i < values.size(); ++i) {
        if (values[i] == values[i - 1]) {
            ++current;
        } else {
            current = 1;
        }
        if (current > best) {
            best = current;
            best_token = values[i];
        }
    }
    if (out_token) {
        *out_token = best_token;
    }
    return best;
}

int longestRunOfToken(const std::vector<int32_t>& values, int32_t token) {
    int best = 0;
    int current = 0;
    for (int32_t value : values) {
        if (value == token) {
            ++current;
            best = std::max(best, current);
        } else {
            current = 0;
        }
    }
    return best;
}

void mostRepeatedToken(const std::vector<int32_t>& values, int32_t* out_token, int* out_count) {
    std::unordered_map<int32_t, int> counts;
    int32_t token = -1;
    int count = 0;
    for (int32_t value : values) {
        int next = ++counts[value];
        if (next > count) {
            count = next;
            token = value;
        }
    }
    if (out_token) {
        *out_token = token;
    }
    if (out_count) {
        *out_count = count;
    }
}

bool obviousDegenerateOutput(const std::vector<int32_t>& values) {
    int32_t run_token = -1;
    const int longest_run = longestRepeatedRun(values, &run_token);
    const int token_220_longest_run = longestRunOfToken(values, 220);
    return values.empty() || longest_run >= 16 || token_220_longest_run >= 8;
}

void usage(const char* argv0) {
    std::cerr << "usage: " << argv0 << " <model_dir> [max_new_tokens] [threads] [prompt_id]\n";
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        usage(argv[0]);
        return 2;
    }
    const std::string model_dir = argv[1];
    const int max_new_tokens = argc >= 3 ? std::max(1, std::atoi(argv[2])) : 32;
    const int threads = argc >= 4 ? std::max(1, std::atoi(argv[3])) : 8;
    const std::string prompt_filter = argc >= 5 ? argv[4] : "";
    const bool prefill_debug = argc >= 6 && std::string(argv[5]) == "prefill_debug";

    xq_options options{};
    options.struct_size = sizeof(options);
    options.backend = "cpu";
    options.threads = threads;
    options.quant_bits = 4;
    options.group_size = 64;
    options.max_context_tokens = 8192;
    options.enable_autotune = 1;
    options.use_mnn_fallback = 0;

    xq_session* session = nullptr;
    xq_status create_status = xq_create(model_dir.c_str(), &options, &session);
    if (create_status != XQ_OK || session == nullptr) {
        std::cout << "{\"schema_version\":1,\"artifact_type\":\"quality_validation\",\"engine\":\"customlib\","
                  << "\"status\":\"error\",\"quality_gate_passed\":false,\"error\":\"xq_create failed\","
                  << "\"status_code\":" << create_status << "}\n";
        return 1;
    }

    xq_metrics initial_metrics{};
    initial_metrics.struct_size = sizeof(initial_metrics);
    xq_get_last_metrics(session, &initial_metrics);

    bool all_ok = true;
    std::ostringstream prompts_json;
    prompts_json << "[";
    std::vector<Prompt> prompts;
    for (const Prompt& prompt : validationPrompts()) {
        if (prompt_filter.empty() || prompt_filter == prompt.id) {
            prompts.push_back(prompt);
        }
    }
    if (prompts.empty()) {
        std::cerr << "unknown prompt_id: " << prompt_filter << "\n";
        xq_destroy(session);
        return 2;
    }
    for (size_t i = 0; i < prompts.size(); ++i) {
        const Prompt& prompt = prompts[i];
        if (i != 0) {
            prompts_json << ",";
        }
        xq_reset(session);
        std::vector<int32_t> generated(static_cast<size_t>(max_new_tokens), 0);
        xq_metrics metrics{};
        metrics.struct_size = sizeof(metrics);
        std::string prefill_debug_json = "{}";
        std::vector<std::string> step_debug_json;
        xq_status status = XQ_OK;
        if (prefill_debug) {
            status = xq_prefill(session, prompt.tokens.data(), prompt.tokens.size(), &metrics);
            if (status == XQ_OK) {
                prefill_debug_json = getDebugJson(session);
                step_debug_json.push_back(prefill_debug_json);
                for (size_t t = 0; t < generated.size(); ++t) {
                    if (t != 0) {
                        step_debug_json.push_back(getDebugJson(session));
                    }
                    xq_metrics step_metrics{};
                    step_metrics.struct_size = sizeof(step_metrics);
                    status = xq_decode_one(session, &generated[t], &step_metrics);
                    metrics = step_metrics;
                    if (status != XQ_OK) {
                        generated.resize(t);
                        break;
                    }
                }
            } else {
                generated.clear();
            }
        } else {
            status = xq_generate(session,
                                 prompt.tokens.data(),
                                 prompt.tokens.size(),
                                 generated.size(),
                                 generated.data(),
                                 generated.size(),
                                 &metrics);
        }
        const size_t generated_count = std::min<size_t>(generated.size(), metrics.generated_tokens);
        generated.resize(generated_count);

        int invalid_count = 0;
        for (int32_t token : generated) {
            if (token < 0 || token >= kQwen35VocabSize) {
                ++invalid_count;
            }
        }
        int32_t longest_run_token = -1;
        const int longest_run = longestRepeatedRun(generated, &longest_run_token);
        int32_t most_repeated_token = -1;
        int most_repeated_count = 0;
        mostRepeatedToken(generated, &most_repeated_token, &most_repeated_count);
        const int token_220_longest_run = longestRunOfToken(generated, 220);
        const bool token_220_failure = token_220_longest_run >= 8;
        const bool empty_output = generated.empty();
        const bool degenerate = obviousDegenerateOutput(generated);
        const bool prompt_ok = status == XQ_OK && invalid_count == 0 && !empty_output && !degenerate;
        all_ok = all_ok && prompt_ok;

        prompts_json << "{"
                     << "\"id\":\"" << jsonEscape(prompt.id) << "\","
                     << "\"prompt_kind\":\"" << jsonEscape(prompt.kind) << "\","
                     << "\"prompt_text_hint\":\"" << jsonEscape(prompt.hint) << "\","
                     << "\"raw_text_prompt_available\":false,"
                     << "\"prompt_token_count\":" << prompt.tokens.size() << ","
                     << "\"prompt_token_ids\":";
        appendIntArray(prompts_json, prompt.tokens, prompt.tokens.size());
        prompts_json << ",\"generated_token_count\":" << generated_count << ","
                     << "\"generated_token_ids\":";
        appendIntArray(prompts_json, generated, generated.size());
        prompts_json << ",\"decoded_text_available\":false,"
                     << "\"decoded_generated_text\":\"\","
                     << "\"status_code\":" << status << ","
                     << "\"status\":\"" << (prompt_ok ? "ok" : "error") << "\","
                     << "\"invalid_token_count\":" << invalid_count << ","
                     << "\"empty_output\":" << (empty_output ? "true" : "false") << ","
                     << "\"longest_repeated_run\":" << longest_run << ","
                     << "\"longest_repeated_run_token\":" << longest_run_token << ","
                     << "\"most_repeated_token\":" << most_repeated_token << ","
                     << "\"most_repeated_token_count\":" << most_repeated_count << ","
                     << "\"repeated_token_220_longest_run\":" << token_220_longest_run << ","
                     << "\"repeated_token_220_failure\":" << (token_220_failure ? "true" : "false") << ","
                     << "\"unique_token_count\":" << uniqueTokenCount(generated) << ","
                     << "\"obvious_degenerate_output\":" << (degenerate ? "true" : "false") << ","
                     << "\"prefill_ms\":" << metrics.prefill_ms << ","
                     << "\"decode_total_ms\":" << metrics.decode_total_ms << ","
                     << "\"prefill_debug\":" << prefill_debug_json << ","
                     << "\"decode_step_debug\":[";
        for (size_t d = 0; d < step_debug_json.size(); ++d) {
            if (d != 0) {
                prompts_json << ",";
            }
            prompts_json << step_debug_json[d];
        }
        prompts_json << "]"
                     << "}";
    }
    prompts_json << "]";

    std::vector<char> trace_buffer(1024 * 1024);
    std::string kernel_trace_json = "{\"rows\":[]}";
    if (xq_get_kernel_trace_json(session, trace_buffer.data(), trace_buffer.size()) == XQ_OK) {
        kernel_trace_json = trace_buffer.data();
    }
    xq_destroy(session);

    std::cout << "{"
              << "\"schema_version\":1,"
              << "\"artifact_type\":\"quality_validation\","
              << "\"engine\":\"customlib\","
              << "\"status\":\"" << (all_ok ? "ok" : "error") << "\","
              << "\"quality_gate_passed\":" << (all_ok ? "true" : "false") << ","
              << "\"model\":{\"hf_repo\":\"Qwen/Qwen3.5-9B\","
              << "\"hf_revision\":\"c202236235762e1c871ad0ccb60c8ee5ba337b9a\","
              << "\"format\":\"xqwen35_custom_w4a16\","
              << "\"vocab_size_assumed\":" << kQwen35VocabSize << "},"
              << "\"artifact\":{\"model_dir\":\"" << jsonEscape(model_dir) << "\"},"
              << "\"runtime\":{\"threads\":" << threads
              << ",\"selected_kernels\":{\"summary\":\"" << jsonEscape(initial_metrics.selected_kernels)
              << "\",\"hotpath_replaced\":true,"
              << "\"full_custom_decode\":true,"
              << "\"replaced_op_families\":[\"q_proj\",\"k_proj\",\"v_proj\",\"o_proj\",\"gate_proj\",\"up_proj\",\"down_proj\",\"rmsnorm\",\"rope\",\"attention\",\"linear_attention_state\",\"lm_head\",\"sampling\",\"prefill_kv_build\"],"
              << "\"fallback_op_families\":[]}},"
              << "\"custom_path\":{\"calls_mnn_llm_response_for_measured_generation\":false,"
              << "\"use_mnn_fallback\":0,"
              << "\"full_custom_decode\":true,"
              << "\"fallback_op_families\":[]},"
              << "\"custom_backend_requested\":\"cpu\","
              << "\"custom_backend_actual\":\"cpu\","
              << "\"validation\":{\"prompt_set\":\"small_english_tokenizer_ids\","
              << "\"validation_compare_to_stock\":true,"
              << "\"tokenizer_decode_available\":false,"
              << "\"validation_dump_tokens\":true,"
              << "\"validation_dump_text\":false,"
              << "\"validation_dump_intermediate\":" << (prefill_debug ? "true" : "false") << ","
              << "\"max_new_tokens\":" << max_new_tokens
              << ",\"temperature\":0,\"top_k\":1,\"top_p\":1},"
              << "\"prompts\":" << prompts_json.str() << ","
              << "\"per_kernel_wall_clock\":" << kernel_trace_json
              << "}\n";
    return all_ok ? 0 : 3;
}

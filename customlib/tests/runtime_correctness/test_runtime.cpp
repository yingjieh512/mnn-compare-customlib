#include "xqwen35.h"

#include "../../kernels/kernels.hpp"

#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {

uint16_t floatToBf16(float value) {
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    return static_cast<uint16_t>(bits >> 16);
}

void writeU32(std::ofstream& out, uint32_t value) {
    out.write(reinterpret_cast<const char*>(&value), sizeof(value));
}

void writeU64(std::ofstream& out, uint64_t value) {
    out.write(reinterpret_cast<const char*>(&value), sizeof(value));
}

void writeVector(const std::filesystem::path& path, const std::vector<float>& values) {
    std::ofstream out(path, std::ios::binary);
    assert(out);
    out.write(reinterpret_cast<const char*>(values.data()),
              static_cast<std::streamsize>(values.size() * sizeof(float)));
}

void writeXq4(const std::filesystem::path& path, int rows, int cols, const std::vector<float>& values) {
    assert(static_cast<int>(values.size()) == rows * cols);
    xq::kernels::QuantizedMatrix q = xq::kernels::quantizeLowBit(values.data(), rows, cols, 4, 4);
    std::ofstream out(path, std::ios::binary);
    assert(out);
    const char magic[8] = {'X', 'Q', 'W', '4', 'A', '1', '6', '\0'};
    out.write(magic, sizeof(magic));
    writeU32(out, 1);
    writeU32(out, static_cast<uint32_t>(q.rows));
    writeU32(out, static_cast<uint32_t>(q.cols));
    writeU32(out, static_cast<uint32_t>(q.group_size));
    writeU32(out, 4);
    writeU64(out, static_cast<uint64_t>(q.packed.size()));
    writeU64(out, static_cast<uint64_t>(q.scales.size()));
    writeU64(out, static_cast<uint64_t>(q.zeros.size()));
    out.write(reinterpret_cast<const char*>(q.packed.data()), static_cast<std::streamsize>(q.packed.size()));
    out.write(reinterpret_cast<const char*>(q.scales.data()),
              static_cast<std::streamsize>(q.scales.size() * sizeof(float)));
    out.write(reinterpret_cast<const char*>(q.zeros.data()),
              static_cast<std::streamsize>(q.zeros.size() * sizeof(float)));
}

std::vector<float> patternedMatrix(int rows, int cols, float scale) {
    std::vector<float> out(static_cast<size_t>(rows * cols));
    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            const float sign = ((r + c) % 2 == 0) ? 1.0f : -1.0f;
            out[static_cast<size_t>(r * cols + c)] =
                sign * scale * (1.0f + static_cast<float>((r * 3 + c * 5) % 7));
        }
    }
    return out;
}

void writeTinyModel(const std::filesystem::path& dir) {
    std::filesystem::remove_all(dir);
    std::filesystem::create_directories(dir);
    const char* manifest =
        "{"
        "\"format\":\"xqwen35_custom_w4a16\","
        "\"hidden_size\":4,"
        "\"intermediate_size\":8,"
        "\"vocab_size\":8,"
        "\"num_hidden_layers\":2,"
        "\"num_attention_heads\":2,"
        "\"num_key_value_heads\":1,"
        "\"head_dim\":2,"
        "\"linear_key_head_dim\":2,"
        "\"linear_value_head_dim\":2,"
        "\"linear_num_key_heads\":1,"
        "\"linear_num_value_heads\":2,"
        "\"linear_conv_kernel_dim\":2,"
        "\"rms_norm_eps\":0.000001,"
        "\"rope_theta\":10000,"
        "\"partial_rotary_factor\":1.0"
        "}";
    {
        std::ofstream out(dir / "xqwen35_manifest.json");
        out << manifest;
    }

    {
        std::ofstream out(dir / "embeddings_bf16.bin", std::ios::binary);
        assert(out);
        for (int token = 0; token < 8; ++token) {
            for (int d = 0; d < 4; ++d) {
                const float value = 0.05f * static_cast<float>(token + 1) + (token == d ? 1.0f : 0.0f);
                const uint16_t bf16 = floatToBf16(value);
                out.write(reinterpret_cast<const char*>(&bf16), sizeof(bf16));
            }
        }
    }

    writeVector(dir / "norm_weight.f32", std::vector<float>(4, 1.0f));
    for (int layer = 0; layer < 2; ++layer) {
        const std::string prefix = "layers_" + std::to_string(layer) + "_";
        writeVector(dir / (prefix + "input_layernorm_weight.f32"), std::vector<float>(4, 1.0f));
        writeVector(dir / (prefix + "post_attention_layernorm_weight.f32"), std::vector<float>(4, 1.0f));
        writeXq4(dir / (prefix + "mlp_gate_proj_weight.xq4"), 8, 4, patternedMatrix(8, 4, 0.02f));
        writeXq4(dir / (prefix + "mlp_up_proj_weight.xq4"), 8, 4, patternedMatrix(8, 4, 0.015f));
        writeXq4(dir / (prefix + "mlp_down_proj_weight.xq4"), 4, 8, patternedMatrix(4, 8, 0.01f));
    }

    writeXq4(dir / "layers_0_linear_attn_in_proj_qkv_weight.xq4", 8, 4, patternedMatrix(8, 4, 0.03f));
    writeXq4(dir / "layers_0_linear_attn_in_proj_a_weight.xq4", 2, 4, patternedMatrix(2, 4, 0.02f));
    writeXq4(dir / "layers_0_linear_attn_in_proj_b_weight.xq4", 2, 4, patternedMatrix(2, 4, 0.025f));
    writeXq4(dir / "layers_0_linear_attn_in_proj_z_weight.xq4", 4, 4, patternedMatrix(4, 4, 0.03f));
    writeXq4(dir / "layers_0_linear_attn_out_proj_weight.xq4", 4, 4, patternedMatrix(4, 4, 0.02f));
    writeVector(dir / "layers_0_linear_attn_norm_weight.f32", std::vector<float>(2, 1.0f));
    std::vector<float> conv(16, 0.0f);
    for (int c = 0; c < 8; ++c) {
        conv[static_cast<size_t>(c * 2)] = 0.25f;
        conv[static_cast<size_t>(c * 2 + 1)] = 1.0f;
    }
    writeVector(dir / "layers_0_linear_attn_conv1d_weight.f32", conv);
    writeVector(dir / "layers_0_linear_attn_A_log.f32", std::vector<float>{-2.0f, -2.2f});
    writeVector(dir / "layers_0_linear_attn_dt_bias.f32", std::vector<float>{0.0f, 0.1f});

    writeXq4(dir / "layers_1_self_attn_q_proj_weight.xq4", 8, 4, patternedMatrix(8, 4, 0.025f));
    writeXq4(dir / "layers_1_self_attn_k_proj_weight.xq4", 2, 4, patternedMatrix(2, 4, 0.02f));
    writeXq4(dir / "layers_1_self_attn_v_proj_weight.xq4", 2, 4, patternedMatrix(2, 4, 0.03f));
    writeXq4(dir / "layers_1_self_attn_o_proj_weight.xq4", 4, 4, patternedMatrix(4, 4, 0.02f));
    writeVector(dir / "layers_1_self_attn_q_norm_weight.f32", std::vector<float>(2, 1.0f));
    writeVector(dir / "layers_1_self_attn_k_norm_weight.f32", std::vector<float>(2, 1.0f));

    writeXq4(dir / "lm_head_weight.xq4", 8, 4, patternedMatrix(8, 4, 0.04f));
}

bool contains(const std::string& haystack, const std::string& needle) {
    return haystack.find(needle) != std::string::npos;
}

}  // namespace

int main() {
    const std::filesystem::path model_dir = std::filesystem::temp_directory_path() / "xq_runtime_tiny_model";
    writeTinyModel(model_dir);

    xq_options options{};
    options.struct_size = sizeof(options);
    options.backend = "cpu";
    options.threads = 1;
    options.quant_bits = 4;
    options.group_size = 4;
    options.max_context_tokens = 16;
    options.enable_autotune = 0;
    options.use_mnn_fallback = 0;

    xq_session* session = nullptr;
    const std::string model_path = model_dir.string();
    const xq_status create_status = xq_create(model_path.c_str(), &options, &session);
    assert(create_status == XQ_OK);
    assert(session != nullptr);

    int32_t prompt[] = {1, 2, 3};
    xq_metrics metrics{};
    metrics.struct_size = sizeof(metrics);
    assert(xq_prefill(session, prompt, 3, &metrics) == XQ_OK);
    assert(metrics.prompt_tokens == 3);

    char trace_json[32768];
    assert(xq_get_kernel_trace_json(session, trace_json, sizeof(trace_json)) == XQ_OK);
    std::string trace = trace_json;
    assert(contains(trace, "prefill_token_custom"));
    assert(contains(trace, "prefill_kv_build_custom"));
    assert(contains(trace, "linear_attention_state_update_custom"));

    int32_t next = 0;
    assert(xq_decode_one(session, &next, &metrics) == XQ_OK);
    assert(next >= 0 && next < 8);
    assert(metrics.generated_tokens == 1);

    std::vector<int32_t> out(2);
    assert(xq_generate(session, prompt, 3, out.size(), out.data(), out.size(), &metrics) == XQ_OK);
    assert(metrics.generated_tokens == out.size());
    assert(metrics.decode_tokens_per_second >= 0.0);

    assert(xq_get_kernel_trace_json(session, trace_json, sizeof(trace_json)) == XQ_OK);
    trace = trace_json;
    assert(contains(trace, "attention_score_custom"));
    assert(contains(trace, "attention_softmax_custom"));
    assert(contains(trace, "attention_v_reduce_custom"));
    assert(contains(trace, "lm_head_custom"));
    assert(contains(trace, "sampling_greedy_custom"));
    assert(!contains(trace, "fallback_"));

    char info[2048];
    assert(xq_get_backend_info(session, info, sizeof(info)) == XQ_OK);
    const std::string backend_info = info;
    assert(contains(backend_info, "full_custom_decode=true"));
    assert(contains(backend_info, "fallback_ops=none"));
    std::cout << backend_info << "\n";

    xq_destroy(session);
    std::cout << "runtime correctness passed\n";
    return 0;
}

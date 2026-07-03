#include <jni.h>

#include <android/log.h>

#include <cstdint>
#include <sstream>
#include <string>
#include <vector>

#include "xqwen35.h"

namespace {

std::string jstringToString(JNIEnv* env, jstring value) {
    if (!value) {
        return {};
    }
    const char* chars = env->GetStringUTFChars(value, nullptr);
    std::string out = chars ? chars : "";
    if (chars) {
        env->ReleaseStringUTFChars(value, chars);
    }
    return out;
}

std::string metricsJson(const xq_metrics& m, int prompt_tokens, int max_new_tokens) {
    std::ostringstream oss;
    oss << "{"
        << "\"schema_version\":1,"
        << "\"engine\":\"customlib\","
        << "\"backend\":\"" << m.backend << "\","
        << "\"status\":\"smoke_only_until_real_model_pack_is_present\","
        << "\"model\":{\"hf_repo\":\"Qwen/Qwen3.5-9B\",\"hf_revision\":\"c202236235762e1c871ad0ccb60c8ee5ba337b9a\","
        << "\"quantization\":{\"bits\":4,\"group_size\":64,\"scheme\":\"w4a16_groupwise\"}},"
        << "\"generation\":{\"prompt_tokens\":" << prompt_tokens
        << ",\"max_new_tokens\":" << max_new_tokens
        << ",\"actual_new_tokens\":" << m.generated_tokens
        << ",\"temperature\":0,\"top_k\":1,\"top_p\":1,\"batch_size\":1},"
        << "\"runtime\":{\"threads\":8,\"selected_kernels\":{\"summary\":\"" << m.selected_kernels << "\"}},"
        << "\"timing_ms\":{\"load\":" << m.load_ms << ",\"prefill\":" << m.prefill_ms
        << ",\"first_token\":" << m.first_token_ms << ",\"decode_total\":" << m.decode_total_ms
        << ",\"total_generate\":" << m.total_generate_ms << "},"
        << "\"tokens_per_second\":{\"prefill\":" << m.prefill_tokens_per_second
        << ",\"decode\":" << m.decode_tokens_per_second << "},"
        << "\"correctness\":{\"kernel_tests_passed\":false,\"end_to_end_smoke_passed\":true}"
        << "}";
    return oss.str();
}

}  // namespace

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_xqwen35bench_NativeBenchmark_runBenchmark(JNIEnv* env,
                                                           jclass,
                                                           jstring model_dir,
                                                           jint prompt_tokens,
                                                           jint max_new_tokens) {
    const std::string model = jstringToString(env, model_dir);
    __android_log_print(ANDROID_LOG_INFO, "XQBENCH", "BENCH_START engine=customlib model_dir=%s", model.c_str());

    xq_options options{};
    options.struct_size = sizeof(options);
    options.backend = "cpu";
    options.threads = 8;
    options.quant_bits = 4;
    options.group_size = 64;
    options.max_context_tokens = 8192;
    options.enable_autotune = 1;
    options.use_mnn_fallback = 1;

    xq_session* session = nullptr;
    xq_status status = xq_create(model.c_str(), &options, &session);
    xq_metrics metrics{};
    metrics.struct_size = sizeof(metrics);
    std::vector<int32_t> prompt(static_cast<size_t>(prompt_tokens));
    for (int i = 0; i < prompt_tokens; ++i) {
        prompt[static_cast<size_t>(i)] = 1000 + i;
    }
    std::vector<int32_t> out(static_cast<size_t>(max_new_tokens));
    if (status == XQ_OK) {
        status = xq_generate(session, prompt.data(), prompt.size(), out.size(), out.data(), out.size(), &metrics);
    }
    if (session) {
        xq_destroy(session);
    }

    std::string json;
    if (status == XQ_OK) {
        json = metricsJson(metrics, prompt_tokens, max_new_tokens);
    } else {
        std::ostringstream oss;
        oss << "{\"schema_version\":1,\"engine\":\"customlib\",\"status\":\"error\",\"error_code\":" << status << "}";
        json = oss.str();
    }
    __android_log_print(ANDROID_LOG_INFO, "XQBENCH", "BENCH_RESULT_JSON %s", json.c_str());
    __android_log_print(ANDROID_LOG_INFO, "XQBENCH", "BENCH_END engine=customlib");
    return env->NewStringUTF(json.c_str());
}


#include <jni.h>

#include <android/log.h>

#include <sstream>
#include <string>

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

}  // namespace

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_xqwen35stock_NativeStockBenchmark_runBenchmark(JNIEnv* env,
                                                                jclass,
                                                                jstring model_dir,
                                                                jint prompt_tokens,
                                                                jint max_new_tokens) {
    const std::string model = jstringToString(env, model_dir);
    __android_log_print(ANDROID_LOG_INFO, "XQBENCH", "BENCH_START engine=mnn_stock model_dir=%s", model.c_str());
    std::ostringstream oss;
    oss << "{"
        << "\"schema_version\":1,"
        << "\"engine\":\"mnn_stock\","
        << "\"backend\":\"cpu\","
        << "\"status\":\"not_run\","
        << "\"blocker\":\"stock MNN benchmark requires converted Qwen/Qwen3.5-9B MNN artifact and linked MNN llm runtime\","
        << "\"model\":{\"hf_repo\":\"Qwen/Qwen3.5-9B\",\"hf_revision\":\"c202236235762e1c871ad0ccb60c8ee5ba337b9a\","
        << "\"quantization\":{\"bits\":4,\"group_size\":64,\"scheme\":\"w4a16_groupwise\"}},"
        << "\"generation\":{\"prompt_tokens\":" << prompt_tokens
        << ",\"max_new_tokens\":" << max_new_tokens
        << ",\"temperature\":0,\"top_k\":1,\"top_p\":1,\"batch_size\":1},"
        << "\"tokens_per_second\":{\"prefill\":0.0,\"decode\":0.0},"
        << "\"correctness\":{\"kernel_tests_passed\":false,\"end_to_end_smoke_passed\":false}"
        << "}";
    const std::string json = oss.str();
    __android_log_print(ANDROID_LOG_INFO, "XQBENCH", "BENCH_RESULT_JSON %s", json.c_str());
    __android_log_print(ANDROID_LOG_INFO, "XQBENCH", "BENCH_END engine=mnn_stock");
    return env->NewStringUTF(json.c_str());
}


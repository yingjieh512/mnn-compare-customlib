# Connector Walkthrough

The final v16 benchmark separates four connector roles: stock MNN baseline, optional compatibility fallback, JNI benchmark entry points, and AWS Device Farm artifact collection. The complete final walkthrough is in `docs/kernel_library_code_walkthrough_final.md`.

## MNN Baseline Connector

The stock baseline stays unmodified and is implemented in `android/app/src/main/cpp/stock_benchmark_jni.cpp`.

- Creates `MNN::Transformer::Llm`.
- Runs the stock generation path.
- Reports stock prefill TPS, decode TPS, and TPOT.
- Emits `BENCH_RESULT_JSON` for Device Farm artifacts.

This is the only measured path that uses MNN generation.

## Custom Runtime Connector

The measured custom path enters through `customlib/include/xqwen35.h` and is implemented by `customlib/runtime/session.cpp`.

- `xq_create` loads `CustomModel` when `xq_options.use_mnn_fallback = 0`.
- `xq_generate` dispatches to custom prefill and custom decode.
- `xq_get_kernel_trace_json` returns per-kernel wall-clock rows from the custom path.

Final Device Farm evidence reports:

```text
use_mnn_fallback = 0
calls_mnn_llm_response_for_measured_generation = false
full_custom_decode = true
fallback_op_families = []
```

## Fallback Connector

`Session` still supports `xq_options.use_mnn_fallback != 0` for compatibility and debugging. That mode creates an MNN LLM session.

The final measured custom benchmark does not use this connector. It remains separate from the final `BENCH_RESULT_JSON` custom generation loop.

## JNI Connector

The Android instrumentation entry points are:

- `NativeStockBenchmark.runBenchmark(...)`
- `NativeBenchmark.runBenchmark(...)`

Both pass the same model directory, prompt token count, max new tokens, prompt token id, warmup count, and measured count. Both write the JSON result into the Device Farm artifact directory.

## Benchmark Connector

The custom benchmark JSON records:

- selected kernels and op family coverage
- full custom decode booleans
- empty fallback family list
- per-run prefill/decode timings
- mean prefill TPS, decode TPS, and decode TPOT
- per-kernel wall-clock rows
- MNN hot-path trace evidence collected outside the measured custom loop

## Device Farm Connector

The Android bootstrap downloads split Qwen3.5-9B package parts, reassembles the zip, verifies the full SHA-256 on-device, unzips the model, and then runs instrumentation.

Final runs:

- Stock MNN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/baed9f8e-2a52-4b93-8584-60c305b73757`
- Customlib: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7bc0f1d8-7640-4574-8309-da6bdb9fa642`

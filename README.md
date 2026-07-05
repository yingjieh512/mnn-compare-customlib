# Qwen3.5-9B Custom Mobile Inference Library

This repository builds and benchmarks a custom Android inference library for `Qwen/Qwen3.5-9B` against stock MNN on AWS Device Farm.

Final pinned inputs:

- MNN: `0bff03cbef43c783f44e41484b9f8a0b28bd758d`
- Hugging Face model: `Qwen/Qwen3.5-9B`
- HF revision: `c202236235762e1c871ad0ccb60c8ee5ba337b9a`
- Custom quantization: W4A16 groupwise, group size 64
- Final model package SHA-256: `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`

## Final Status

The v16 final run is complete. Stock MNN and the custom library ran on the same AWS Device Farm Samsung Galaxy S26 Ultra pool with the same Qwen3.5-9B package, same 512-token prompt, same 256-token decode length, greedy settings, CPU backend, and 1 warmup / 3 measured iterations.

The measured custom path is full custom generation:

- `use_mnn_fallback = 0`
- `custom_path.calls_mnn_llm_response_for_measured_generation = false`
- `runtime.selected_kernels.full_custom_decode = true`
- `runtime.selected_kernels.hotpath_replaced = true`
- `runtime.selected_kernels.fallback_op_families = []`

Final performance result:

| Metric | Stock MNN | Customlib | Custom / Stock |
| --- | ---: | ---: | ---: |
| Prefill TPS | 45.0960 | 0.486717 | 0.0108x |
| Decode TPS | 2.28587 | 0.424895 | 0.1859x |
| Decode TPOT | 437.470 ms | 2,353.52 ms | 5.38x stock TPOT |

Speedup verdict: no custom speedup is claimed. The final custom path is complete and verifiable, but stock MNN is 5.38x faster on decode TPS for this run.

Final evidence:

- Final report: `results/reports/final_devicefarm_report.md`
- Machine-readable summary: `results/reports/final_devicefarm_report.json`
- Stock evidence JSON: `results/reports/evidence/stock_mnn_benchmark_v16_final.json`
- Custom evidence JSON: `results/reports/evidence/customlib_benchmark_v16_final.json`
- Code walkthrough: `docs/kernel_library_code_walkthrough_final.md`

Final AWS Device Farm runs:

- Stock MNN run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/baed9f8e-2a52-4b93-8584-60c305b73757`
- Customlib run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7bc0f1d8-7640-4574-8309-da6bdb9fa642`
- Device pool ARN: `arn:aws:devicefarm:us-west-2:884244642857:devicepool:64d2cc31-abd6-49f8-97da-162f82410bc0/14d31c96-b8fc-4930-99c7-1a8948124213`
- Device ARN: `arn:aws:devicefarm:us-west-2::device:536B9FDAEAA14A11B504A3ECC86DA717`

## What The Custom Library Replaces

The final measured custom path replaces the requested decode and prefill families:

- `q_proj`, `k_proj`, `v_proj`, `o_proj`
- `gate_proj`, `up_proj`, `down_proj`
- `rmsnorm`
- `rope`
- `attention`
- `linear_attention_state`
- `lm_head`
- `sampling`
- `prefill_kv_build`

The public ABI is in `customlib/include/xqwen35.h`. The measured Android custom benchmark enters the library through `xq_generate`, then runs `Session::prefill`, `Session::decodeOne`, and `CustomModel` without calling `MNN::Transformer::Llm::response`.

## Build Host Correctness Tests

```powershell
$env:PATH = "C:\msys64\ucrt64\bin;$env:PATH"
cmake -S . -B build-host -G Ninja -DXQ_BUILD_TESTS=ON
cmake --build build-host
ctest --test-dir build-host --output-on-failure
```

Final host result: 2/2 tests passed.

Covered checks include stable softmax, grouped-query attention decode, KV cache append/read, RoPE sanity, RMSNorm sanity, W4A16 GEMV against reference, lm_head argmax, greedy sampling, prefill KV cache length, and tiny end-to-end custom decode.

## Build Android APKs

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_android.ps1
```

Final APK outputs:

- `android/app/build/outputs/apk/debug/stock_mnn_benchmark-debug.apk`
- `android/app/build/outputs/apk/androidTest/debug/stock_mnn_benchmark-debug-androidTest.apk`
- `android/benchmark_app/build/outputs/apk/debug/customlib_benchmark-debug.apk`
- `android/benchmark_app/build/outputs/apk/androidTest/debug/customlib_benchmark-debug-androidTest.apk`

## Model Packing

The final packer is `customlib/packer/pack_qwen35_xq4.py`. It exports W4A16 matrices and runtime metadata for:

- full-attention projections and MLP projections
- Qwen3.5 linear-attention tensors
- `lm_head.weight`
- embeddings and norm vectors
- model dimensions, head counts, RoPE metadata, and quantization metadata

The Device Farm bootstrap reassembled and verified the three-part v15/v16 model package on-device before each final run.

## AWS Device Farm Flow

The automation scripts in `scripts/aws` create or reuse the project and device pool, upload APKs, schedule instrumentation runs, wait for completion, download artifacts, and parse `BENCH_RESULT_JSON`.

The final report records the exact run ARNs, artifact paths, model SHA-256 verification, overall TPOT/TPS, custom per-kernel wall clock, MNN hot-path trace tables, and custom op coverage.

## Honesty Rules

This repository only claims results that are backed by artifacts. The final v16 result is a faithful same-device stock-vs-custom benchmark, but it is not a speedup result. Historical v13/v14 reports remain in `results/reports` for audit trail and are superseded by the v16 final report.

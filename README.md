# Qwen3.5-9B Custom Mobile Inference Library

This repository builds and benchmarks a custom Android inference library for `Qwen/Qwen3.5-9B` against stock MNN on AWS Device Farm.

Final pinned inputs:

- MNN: `0bff03cbef43c783f44e41484b9f8a0b28bd758d`
- Hugging Face model: `Qwen/Qwen3.5-9B`
- HF revision: `c202236235762e1c871ad0ccb60c8ee5ba337b9a`
- Custom quantization: W4A16 groupwise, group size 64
- Final model package SHA-256: `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`

## Final Status

The v17 final backend sweep is complete. Stock MNN CPU, stock MNN Vulkan-request, custom CPU, and custom CPU/Vulkan-hybrid-request were scheduled on the same AWS Device Farm Samsung Galaxy S26 Ultra pool with the same Qwen3.5-9B package, same 512-token prompt, same 256-token decode length, greedy settings, and 1 warmup / 3 measured iterations.

The measured custom generation path is full custom CPU generation:

- `use_mnn_fallback = 0`
- `custom_path.calls_mnn_llm_response_for_measured_generation = false`
- `runtime.selected_kernels.full_custom_decode = true`
- `runtime.selected_kernels.hotpath_replaced = true`
- `runtime.selected_kernels.fallback_op_families = []`

Vulkan was attempted honestly. Stock MNN Vulkan initialized the Adreno Vulkan stack and then crashed before `BENCH_RESULT_JSON`. Custom `cpu_vulkan_hybrid` successfully probed `libvulkan.so` and `vkGetInstanceProcAddr`, but no custom Vulkan kernels were enabled in this build, so the measured generation backend remained CPU. No Vulkan speedup is claimed.

Final performance result:

| Variant | Requested backend | Actual backend | Status | Prefill TPS | Decode TPS | Decode TPOT |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Stock MNN | cpu | cpu | ok | 45.6380 | 2.27746 | 439.086 ms |
| Stock MNN | vulkan | unavailable | crashed before benchmark JSON | n/a | n/a | n/a |
| Customlib | cpu | cpu | ok | 2.13908 | 1.85575 | 538.865 ms |
| Customlib | cpu_vulkan_hybrid | cpu | ok, Vulkan probed but not used for kernels | 2.21477 | 1.93417 | 517.018 ms |

Speedup verdict: no custom speedup is claimed. The best measured custom result is `1.93417 / 2.27746 = 0.8493x` stock CPU decode TPS. The CPU optimization pass improved custom decode materially over v16, but stock MNN remains faster on this device.

## Post-Final Optimization And Quality Guard

A bounded v18r2 optimization attempt later improved measured custom decode performance to `2.14021` TPS / `467.244 ms` TPOT on the same Device Farm pool, but the added deterministic output validation rejected that result. The custom v19r2 quality run produced degenerate repeated token `220` outputs for 4 of 5 validation prompts, exact token match was `0 / 5`, and comparison-gate pass was `0 / 5`.

Per the acceptance rule, v18r2 is not accepted as the official final result. The official final delivery remains the v17 backend sweep above.

- Quality validation report: `results/reports/quality_validation_report.md`
- Stock quality evidence: `results/reports/evidence/quality_validation_v19r2_stock.json`
- Custom quality evidence: `results/reports/evidence/quality_validation_v19r2_custom.json`
- Quality comparison evidence: `results/reports/evidence/quality_validation_v19r2_comparison.json`
- v18/v19 rejection note: `results/reports/optimization_attempt_v18.md`

A later v20 accuracy-debug pass patched concrete graph/runtime mismatches in linear-attention gate math, Qwen3.5 partial RoPE layout, and full-attention q/gate splitting. Host tests passed, but the patched custom APK did not complete Device Farm quality validation; repeated runs stopped before emitting `BENCH_QUALITY_JSON`. This is recorded as a blocker, not a new final result:

- v20 blocker note: `results/reports/quality_debug_blocker.md`
- v20 Device Farm status evidence: `results/reports/evidence/quality_validation_v20_devicefarm_blocker_runs.json`

Final evidence:

- Final report: `results/reports/final_devicefarm_report.md`
- Machine-readable summary: `results/reports/final_devicefarm_report.json`
- Backend sweep summary: `results/reports/evidence/v17_backend_sweep_summary.json`
- Stock CPU evidence JSON: `results/reports/evidence/stock_mnn_cpu_benchmark_v17.json`
- Stock Vulkan failure evidence JSON: `results/reports/evidence/stock_mnn_vulkan_benchmark_failure_v17.json`
- Custom CPU evidence JSON: `results/reports/evidence/customlib_cpu_benchmark_v17.json`
- Custom hybrid-request evidence JSON: `results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v17.json`
- Code walkthrough: `docs/kernel_library_code_walkthrough_final.md`
- Presentation deck: `results/reports/qwen35_9b_v17_backend_sweep_presentation.pptx`
- Presentation contact sheet: `results/reports/qwen35_9b_v17_backend_sweep_presentation_contact_sheet.png`

Final AWS Device Farm runs:

- Stock MNN CPU run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7e44236c-db1a-4900-9fd8-7d8d7d654e28`
- Stock MNN Vulkan-request run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/067c195b-1e14-4bca-998d-c7d38a65c5c7`
- Custom CPU run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/8d765268-aacd-4f52-b845-f5370b4d522f`
- Custom CPU/Vulkan-hybrid-request run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1de54984-c9d9-41d1-81c1-7eed941585ed`
- Device pool ARN: `arn:aws:devicefarm:us-west-2:884244642857:devicepool:64d2cc31-abd6-49f8-97da-162f82410bc0/14d31c96-b8fc-4930-99c7-1a8948124213`

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
cmake -S . -B build-host-opt -G Ninja -DXQ_BUILD_TESTS=ON
cmake --build build-host-opt
ctest --test-dir build-host-opt --output-on-failure
```

Final host result: 2/2 tests passed.

Covered checks include stable softmax, grouped-query attention decode, KV cache append/read, RoPE sanity, RMSNorm sanity, W4A16 GEMV against reference, lm_head argmax, greedy sampling, prefill KV cache length, and tiny end-to-end custom decode.

## Build Android APKs

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_android.ps1
```

The v17 Device Farm runs used rebuilt stock/custom debug APKs plus androidTest APKs from this flow.

## Model Packing

The final packer is `customlib/packer/pack_qwen35_xq4.py`. It exports W4A16 matrices and runtime metadata for:

- full-attention projections and MLP projections
- Qwen3.5 linear-attention tensors
- `lm_head.weight`
- embeddings and norm vectors
- model dimensions, head counts, RoPE metadata, and quantization metadata

The Device Farm bootstrap reassembled and verified the three-part model package on-device before each final run.

## Repository Cleanup

Generated build trees, raw Device Farm artifacts, APKs, ZIPs, model shards, virtualenvs, and local upload specs are ignored. Use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\cleanup_local_artifacts.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\cleanup_local_artifacts.ps1 -Execute
```

The cleanup keeps source, documentation, final reports, and small evidence JSON/TXT/YML files. It keeps the final local model zip unless `-RemoveFinalModelZip` is explicitly passed.

## Honesty Rules

This repository only claims results backed by artifacts. The final v17 result is a faithful same-device full-model stock-vs-custom benchmark. It is not a speedup result, and it does not claim custom Vulkan kernel execution.

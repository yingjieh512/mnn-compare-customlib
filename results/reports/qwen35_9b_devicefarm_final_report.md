# Final Device Farm Report: Qwen3.5-9B Stock MNN vs Customlib v17 Backend Sweep

## Honest Verdict

- Faithful benchmark: YES for the completed CPU comparisons. Stock MNN CPU, custom CPU, and custom CPU/Vulkan-hybrid-request all ran the same full Qwen3.5-9B package on the same AWS Device Farm Samsung Galaxy S26 Ultra pool with the same prompt length, max_new_tokens, greedy settings, warmup count, and measured count.
- Requirement 1 met: YES. The code walkthrough is `docs/kernel_library_code_walkthrough_final.md` and covers the kernel library architecture, generated kernels, public C ABI, JNI connector, stock MNN connector, fallback connector, benchmark connector, Device Farm connector, and Vulkan probe connector.
- Requirement 2 met: YES. This report includes same-device TPOT/TPS, custom per-kernel wall-clock with backend, generated-kernel microbench rows, MNN hot-path trace top op type/name wall-clock rows, Device Farm run ARNs, and evidence file paths.
- Vulkan attempted: YES. Stock MNN Vulkan initialized the Adreno Vulkan stack and then crashed before benchmark JSON. Custom `cpu_vulkan_hybrid` probed `libvulkan.so` and found `vkGetInstanceProcAddr`, but no custom Vulkan kernels were enabled in measured generation.
- Custom Vulkan used in measured generation: NO.
- Custom speedup claim allowed: NO. The best measured custom decode TPS is `1.93417`, while stock MNN CPU decode TPS is `2.27746`; best custom is `0.8493x` stock CPU.

## Device Farm Evidence

- Project ARN: `arn:aws:devicefarm:us-west-2:884244642857:project:64d2cc31-abd6-49f8-97da-162f82410bc0`
- Device pool ARN: `arn:aws:devicefarm:us-west-2:884244642857:devicepool:64d2cc31-abd6-49f8-97da-162f82410bc0/14d31c96-b8fc-4930-99c7-1a8948124213`
- Device: Samsung Galaxy S26 Ultra, model ID SM-S948U1, Android 16.
- Model: `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, W4A16 groupwise quantization, group size 64.
- Full model zip SHA-256 verified on-device: `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`.
- Split package bytes: 4,500,000,000 + 4,500,000,000 + 2,266,405,198 = 11,266,405,198.
- Split SHA-256 values: `3b13bdc4a158b6745f58cfe0dc4c31e485990a50f24d8f14809f5df0e2aa15dc`, `60b8c1d898e4db8b626f750660174f20c05a7e28a43ca11192d58494c3e9211f`, `32d8becc5a77be798a9bc8a3c26509e419942b57aad59f8d4b55310de7248b18`.
- Presentation deck: `results/reports/qwen35_9b_v17_backend_sweep_presentation.pptx`; visual QA contact sheet: `results/reports/qwen35_9b_v17_backend_sweep_presentation_contact_sheet.png`.

| Run | Device Farm run ARN | Result | Evidence |
| --- | --- | --- | --- |
| stock_mnn_cpu_v17_backend_sweep | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7e44236c-db1a-4900-9fd8-7d8d7d654e28` | PASSED | `results/reports/evidence/stock_mnn_cpu_benchmark_v17.json` |
| stock_mnn_vulkan_v17_backend_sweep | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/067c195b-1e14-4bca-998d-c7d38a65c5c7` | PASSED by harness, benchmark process crashed | `results/reports/evidence/stock_mnn_vulkan_benchmark_failure_v17.json` |
| customlib_cpu_v17_backend_sweep | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/8d765268-aacd-4f52-b845-f5370b4d522f` | PASSED | `results/reports/evidence/customlib_cpu_benchmark_v17.json` |
| customlib_cpu_vulkan_hybrid_v17_backend_sweep | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1de54984-c9d9-41d1-81c1-7eed941585ed` | PASSED | `results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v17.json` |

## Same Settings

| Field | Value |
| --- | --- |
| Prompt tokens requested | 512 |
| max_new_tokens | 256 |
| Prompt token id | 16 |
| Temperature / top_k / top_p | 0 / 1 / 1 |
| Batch size | 1 |
| Warmup / measured iterations | 1 / 3 |
| Model package | same verified Qwen3.5-9B W4A16 package |
| Device pool | same Samsung Galaxy S26 Ultra pool |

## Backend Sweep

| Variant | Requested backend | Actual backend | Status | Prefill TPS mean | Decode TPS mean | Decode TPOT mean | Device minutes total |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| Stock MNN | cpu | cpu | ok | 45.6380 | 2.27746 | 439.086 ms | 25.35 |
| Stock MNN | vulkan | unavailable | process crashed before `BENCH_RESULT_JSON` | n/a | n/a | n/a | 18.05 |
| Customlib | cpu | cpu | ok, full custom decode | 2.13908 | 1.85575 | 538.865 ms | 46.41 |
| Customlib | cpu_vulkan_hybrid | cpu | ok, Vulkan probed but no Vulkan kernels used | 2.21477 | 1.93417 | 517.018 ms | 41.80 |

Stock Vulkan evidence: the instrumentation output records `BENCH_START engine=mnn_stock ... backend=vulkan`, Adreno Vulkan driver initialization, `Application Name: MNN_Vulkan`, then MNN messages `The customized gpu mode is illegal for Vulkan backend. Using the default mode.`, `Can't open file: ... tmp/mnn_cachefile.bin`, `Load Cache file error.`, followed by `INSTRUMENTATION_RESULT: shortMsg=Process crashed.` No Vulkan TPS/TPOT is reported because no benchmark JSON was produced.

Custom Vulkan evidence: the custom hybrid-request JSON reports `custom_backend_requested = cpu_vulkan_hybrid`, `custom_backend_actual = cpu`, `vulkan_attempt.status = ok`, `libvulkan_loaded = true`, `vkGetInstanceProcAddr_found = true`, `full_or_hybrid_kernel_status = not_enabled_in_this_build`, and `custom_path.vulkan_generation_kernels_used = false`.

Optional OpenCL, NNAPI, and QNN variants were not run in v17 and are not claimed.

## Overall Comparisons

| Comparison | Decode TPS ratio | Interpretation |
| --- | ---: | --- |
| Custom CPU / Stock CPU | 0.8148x | Custom CPU is slower than stock CPU. |
| Custom hybrid-request actual CPU / Stock CPU | 0.8493x | Best custom v17 run is still slower than stock CPU. |
| Stock Vulkan / Custom hybrid | n/a | Stock Vulkan crashed before metrics; custom hybrid did not execute Vulkan kernels. |
| Best custom / Best stock | 0.8493x | No speedup. |

The v17 CPU optimization pass still matters: v16 custom decode TPS was 0.424895, while v17 custom CPU is 1.85575 TPS and v17 best custom is 1.93417 TPS. That is a large customlib improvement, but it does not beat MNN.

## Custom Path Coverage

Measured custom generation evidence from the v17 JSON:

```text
custom_decode_loop;hotpath_replaced=true;full_custom_decode=true;linear=q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj,linear_attn_qkv_a_b_z_out,lm_head;rmsnorm=custom;rope=custom;attention=custom_gqa_decode;linear_attention_state=custom_gated_delta;sampling=custom_greedy;prefill_kv_build=custom;fallback_ops=none
```

- `runtime.selected_kernels.hotpath_replaced = true`
- `runtime.selected_kernels.full_custom_decode = true`
- `runtime.selected_kernels.fallback_op_families = []`
- `custom_path.use_mnn_fallback = 0`
- `custom_path.calls_mnn_llm_response_for_measured_generation = false`

| Op family | Backend in measured custom path | Replaced? | Fallback? |
| --- | --- | --- | --- |
| q_proj | cpu | yes | no |
| k_proj | cpu | yes | no |
| v_proj | cpu | yes | no |
| o_proj | cpu | yes | no |
| gate_proj | cpu | yes | no |
| up_proj | cpu | yes | no |
| down_proj | cpu | yes | no |
| rmsnorm | cpu | yes | no |
| rope | cpu | yes | no |
| attention | cpu | yes | no |
| linear_attention_state | cpu | yes | no |
| lm_head | cpu | yes | no |
| sampling | cpu | yes | no |
| prefill_kv_build | cpu | yes | no |

## Per-Run Timings

| Engine | Backend requested | Run | Warmup | Prefill ms | Decode ms | Prefill TPS | Decode TPS |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| Stock MNN | cpu | 0 | true | 12,855.747 | 112,843.695 | 39.8265 | 2.26862 |
| Stock MNN | cpu | 1 | false | 11,194.592 | 112,057.582 | 45.7364 | 2.28454 |
| Stock MNN | cpu | 2 | false | 11,231.535 | 113,070.093 | 45.5859 | 2.26408 |
| Stock MNN | cpu | 3 | false | 11,230.103 | 112,095.991 | 45.5917 | 2.28376 |
| Customlib | cpu | 0 | true | 196,579 | 133,584 | 2.60455 | 1.91640 |
| Customlib | cpu | 1 | false | 237,415 | 140,384 | 2.15657 | 1.82357 |
| Customlib | cpu | 2 | false | 240,863 | 136,609 | 2.12569 | 1.87396 |
| Customlib | cpu | 3 | false | 239,815 | 136,918 | 2.13498 | 1.86973 |
| Customlib | cpu_vulkan_hybrid | 0 | true | 189,802 | 125,560 | 2.69754 | 2.03886 |
| Customlib | cpu_vulkan_hybrid | 1 | false | 232,799 | 133,033 | 2.19932 | 1.92434 |
| Customlib | cpu_vulkan_hybrid | 2 | false | 231,519 | 133,006 | 2.21148 | 1.92473 |
| Customlib | cpu_vulkan_hybrid | 3 | false | 229,236 | 131,051 | 2.23351 | 1.95344 |

## Custom Per-Kernel Wall Clock

This table uses the best custom v17 evidence file, `customlib_cpu_vulkan_hybrid_benchmark_v17.json`. The requested backend was `cpu_vulkan_hybrid`, but the actual backend for every measured custom op was CPU.

| Kernel / op family | Op family | Backend | Calls | Total ms | Mean ms | Min ms | Max ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| prefill_token_custom | other | cpu | 512 | 229,233.0 | 447.721 | 408.592 | 500.356 |
| linear_down_proj_w4a16 | down_proj | cpu | 24,576 | 67,884.9 | 2.76224 | 2.47130 | 4.89516 |
| linear_gate_proj_w4a16 | gate_proj | cpu | 24,576 | 67,600.5 | 2.75067 | 2.46677 | 4.33911 |
| linear_up_proj_w4a16 | up_proj | cpu | 24,576 | 67,575.3 | 2.74965 | 2.46927 | 4.47234 |
| linear_attn_in_proj_qkv_w4a16 | linear_attention_projection | cpu | 18,432 | 34,010.2 | 1.84517 | 1.64271 | 3.48099 |
| linear_attention_state_update_custom | linear_attention_state | cpu | 18,432 | 33,135.9 | 1.79774 | 1.66052 | 3.33135 |
| linear_attn_out_proj_w4a16 | linear_attention_projection | cpu | 18,432 | 17,530.3 | 0.951081 | 0.874062 | 4.65776 |
| linear_attn_in_proj_z_w4a16 | linear_attention_projection | cpu | 18,432 | 17,315.7 | 0.939437 | 0.856406 | 2.04536 |
| sampling_greedy_custom | sampling | cpu | 256 | 13,128.4 | 51.2827 | 47.8109 | 59.4392 |
| lm_head_custom | lm_head | cpu | 256 | 13,128.0 | 51.2811 | 47.8095 | 59.4364 |
| attention_score_custom | attention_score | cpu | 6,144 | 11,354.2 | 1.84802 | 0.004323 | 5.34099 |
| linear_q_proj_w4a16 | q_proj | cpu | 6,144 | 11,333.3 | 1.84461 | 1.72526 | 3.16641 |
| linear_o_proj_w4a16 | o_proj | cpu | 6,144 | 5,819.33 | 0.947157 | 0.875208 | 1.93854 |
| attention_v_reduce_custom | attention_v_reduce | cpu | 6,144 | 2,732.98 | 0.444821 | 0.001250 | 1.56917 |
| linear_k_proj_w4a16 | k_proj | cpu | 6,144 | 2,017.68 | 0.328398 | 0.302917 | 1.21349 |
| linear_v_proj_w4a16 | v_proj | cpu | 6,144 | 2,012.41 | 0.327541 | 0.301823 | 1.22781 |
| linear_attention_conv1d_custom | linear_attention_state | cpu | 18,432 | 1,988.89 | 0.107904 | 0.099895 | 0.507604 |
| silu_gate_mul_custom | activation | cpu | 24,576 | 1,502.20 | 0.0611247 | 0.056198 | 0.173177 |
| attention_softmax_custom | attention_softmax | cpu | 6,144 | 184.523 | 0.0300331 | 0.000312 | 0.141302 |
| rmsnorm_input | rmsnorm | cpu | 24,576 | 164.617 | 0.006698 | 0.005833 | 0.052188 |
| rmsnorm_post_attention | rmsnorm | cpu | 24,576 | 164.020 | 0.006674 | 0.005833 | 0.084687 |
| rope_qk_custom | rope | cpu | 6,144 | 148.640 | 0.024193 | 0.016666 | 0.121823 |
| prefill_kv_build_custom | other | cpu | 6,144 | 15.2301 | 0.002479 | 0.001458 | 0.087865 |
| kv_append_custom | other | cpu | 6,144 | 12.5035 | 0.002035 | 0.001146 | 0.086302 |
| rmsnorm_final | rmsnorm | cpu | 768 | 5.58162 | 0.007268 | 0.006145 | 0.020833 |

Note: `sampling_greedy_custom` wraps the greedy section and therefore overlaps with `lm_head_custom`; it should not be summed independently with `lm_head_custom` as exclusive time.

## Generated Kernel Microbench

The microbench ran on the same custom Device Farm APK after measured custom generation completed. It is not used for the overall TPS calculation.

| Kernel | Backend | Implementation | Qwen3.5 shape | Mean wall ms | Median wall ms |
| --- | --- | --- | --- | ---: | ---: |
| gemv_w4a16_attn_4096x4096 | cpu | generated_tiled_neon_fused_dequant_gemv_parallel_group_sum_reuse | attention_or_output_projection | 1.24210 | 1.24281 |
| gemv_w4a16_mlp_up_12288x4096 | cpu | generated_tiled_neon_fused_dequant_gemv_parallel_group_sum_reuse | mlp_gate_or_up_projection | 2.80851 | 2.75448 |
| gemv_w4a16_mlp_down_4096x12288 | cpu | generated_tiled_neon_fused_dequant_gemv_parallel_group_sum_reuse | mlp_down_projection | 2.66151 | 2.38208 |
| rmsnorm_hidden4096 | cpu | customlib_reference | hidden_size | 0.006458 | 0.006458 |
| rope_q_heads16_dim256_pos512 | cpu | customlib_reference | q_heads_x_head_dim | 0.143854 | 0.143802 |
| gqa_decode_ctx512_q16_kv4_dim256 | cpu | customlib_reference | full_attention_layer_decode | 2.43733 | 2.42828 |
| gated_delta_decode_k128_v128 | cpu | customlib_reference | linear_attention_layer_decode | 0.049601 | 0.049583 |

## MNN Hot-Path Trace: Top Op Types

The MNN hot-path trace is a separate debug-callback trace collected inside the custom APK after measured custom generation. It is evidence for MNN op wall-clock hotspots; it is not part of the measured custom generation path.

| Stage | Type | Calls | Total ms | Mean ms |
| --- | --- | ---: | ---: | ---: |
| prefill_or_first_token_inferred | Convolution | 249 | 11,031.5 | 44.3030 |
| decode_inferred | Convolution | 3,984 | 4,322.64 | 1.08500 |
| decode_inferred | UnaryOp | 2,464 | 1,338.08 | 0.543051 |
| prefill_or_first_token_inferred | Raster | 521 | 506.385 | 0.971948 |
| decode_inferred | LinearAttention | 384 | 442.760 | 1.15302 |
| decode_inferred | LayerNorm | 1,680 | 356.286 | 0.212075 |
| prefill_or_first_token_inferred | LinearAttention | 24 | 340.210 | 14.1754 |
| decode_inferred | While | 528 | 272.889 | 0.516836 |
| prefill_or_first_token_inferred | UnaryOp | 154 | 255.923 | 1.66184 |
| prefill_or_first_token_inferred | Attention | 8 | 123.375 | 15.4219 |
| prefill_or_first_token_inferred | BinaryOp | 169 | 121.119 | 0.716680 |
| decode_inferred | Attention | 128 | 96.499 | 0.753898 |

## MNN Hot-Path Trace: Top Op Names

| Stage | Type | Name | Calls | Total ms | Mean ms |
| --- | --- | --- | ---: | ---: | ---: |
| decode_inferred | Convolution | `/lm/lm_head/Linear` | 16 | 243.608 | 15.2255 |
| prefill_or_first_token_inferred | Convolution | `/layers.16/mlp/down_proj/Linear` | 1 | 106.017 | 106.017 |
| prefill_or_first_token_inferred | Convolution | `/layers.19/mlp/down_proj/Linear` | 1 | 102.891 | 102.891 |
| prefill_or_first_token_inferred | Convolution | `/layers.15/mlp/down_proj/Linear` | 1 | 101.129 | 101.129 |
| prefill_or_first_token_inferred | Convolution | `/layers.18/mlp/up_proj/Linear` | 1 | 100.149 | 100.149 |
| prefill_or_first_token_inferred | Convolution | `/layers.21/mlp/up_proj/Linear` | 1 | 99.7169 | 99.7169 |
| prefill_or_first_token_inferred | Convolution | `/layers.21/mlp/down_proj/Linear` | 1 | 99.6633 | 99.6633 |
| prefill_or_first_token_inferred | Convolution | `/layers.19/mlp/gate_proj/Linear` | 1 | 98.4257 | 98.4257 |
| prefill_or_first_token_inferred | Convolution | `/layers.31/mlp/gate_proj/Linear` | 1 | 98.2166 | 98.2166 |
| prefill_or_first_token_inferred | Convolution | `/layers.14/mlp/up_proj/Linear` | 1 | 96.9908 | 96.9908 |

## Code Walkthrough Pointers

- Public ABI: `customlib/include/xqwen35.h`.
- Custom runtime selection: `customlib/runtime/session.cpp` creates `CustomModel` when `use_mnn_fallback = 0`; the Android custom benchmark sets that field to zero.
- Full custom prefill/decode: `customlib/runtime/custom_model.cpp` implements prompt-token prefill, KV append, grouped-query attention, gated-delta linear attention state, final `lm_head_custom`, and greedy sampling.
- Generated W4A16 GEMV: `customlib/kernels/generated/arm64_neon/xq_gemv_w4a16_neon.cpp` uses tiled fused dequant GEMV, persistent worker threads, activation group-sum reuse, and streaming lm_head argmax. The W4 file contains no `gemvLowBitReference` call.
- Packer/exporter: `customlib/packer/pack_qwen35_xq4.py` exports `lm_head.weight`, full-attention projections, MLP projections, linear-attention `in_proj_a`, `in_proj_b`, `conv1d.weight`, `A_log`, and `dt_bias`.
- Stock MNN connector: `android/app/src/main/cpp/stock_benchmark_jni.cpp`.
- Custom JNI/benchmark connector and Vulkan probe: `android/benchmark_app/src/main/cpp/benchmark_jni.cpp`.
- Device Farm bootstrap connector: `android/benchmark_app/src/androidTest/java/com/example/xqwen35bench/ModelBootstrap.java` and the matching stock app bootstrap.

## Test Evidence

- Host: `ctest --test-dir build-host-opt --output-on-failure` -> 2/2 passed (`xq_kernel_correctness`, `xq_runtime_correctness`).
- Android build: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_android.ps1` completed and produced stock/custom debug APKs plus androidTest APKs used in v17 Device Farm runs.
- Device Farm stock CPU v17: PASSED and emitted benchmark JSON.
- Device Farm stock Vulkan v17: process crashed after Vulkan initialization; failure evidence retained.
- Device Farm custom CPU v17: PASSED and emitted benchmark JSON.
- Device Farm custom CPU/Vulkan-hybrid-request v17: PASSED and emitted benchmark JSON; actual measured generation backend was CPU.
- Presentation QA: `slides_test.py results/reports/qwen35_9b_v17_backend_sweep_presentation.pptx` -> passed, no overflow detected.

## Cleanup Evidence

The repo ignores generated build trees, Android build outputs, raw Device Farm downloads, APK/AAB/SO/ZIP/BIN/MNN/XPACK/SAFETENSORS artifacts, virtualenvs, and model directories. `scripts/cleanup_local_artifacts.ps1` and `scripts/cleanup_local_artifacts.sh` remove local raw/build/temp artifacts while preserving source, reports, and small evidence files.

## Final Conclusion

The final custom benchmark is a measured full custom prefill/decode path with no listed fallback families and no measured `MNN::Llm::response` call. Requirement 1 and Requirement 2 are satisfied with v17 Device Farm evidence. The custom path is still slower than stock MNN CPU on the Samsung Galaxy S26 Ultra, so the correct final performance verdict is no speedup claimed.

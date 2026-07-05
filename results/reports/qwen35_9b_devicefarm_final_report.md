# Final Device Farm Report: Qwen3.5-9B Stock MNN vs Customlib v18r2 Optimization Final

## Honest Verdict

- Faithful benchmark: YES for the completed CPU comparisons. Stock MNN CPU v17 and optimized customlib v18r2 ran the same full Qwen3.5-9B W4A16 package on the same AWS Device Farm Samsung Galaxy S26 Ultra pool with the same prompt length, max_new_tokens, greedy settings, warmup count, and measured count.
- Requirement 1 met: YES. The code walkthrough is `docs/kernel_library_code_walkthrough_final.md` and covers the kernel library architecture, generated kernels, public C ABI, JNI connector, stock MNN connector, fallback connector, benchmark connector, Device Farm connector, and Vulkan probe connector.
- Requirement 2 met: YES. This report includes same-device TPOT/TPS, custom per-kernel wall-clock with backend, generated-kernel microbench rows, MNN hot-path trace top op type/name wall-clock rows, Device Farm run ARNs, and evidence file paths.
- Vulkan attempted: YES. Stock MNN Vulkan initialized the Adreno Vulkan stack and then crashed before benchmark JSON. Custom `cpu_vulkan_hybrid` probed `libvulkan.so` and found `vkGetInstanceProcAddr`, but no custom Vulkan kernels were enabled in measured generation.
- Custom Vulkan used in measured generation: NO.
- Custom speedup claim allowed: NO. The optimized custom decode TPS is `2.14021`, while stock MNN CPU decode TPS is `2.27746`; optimized custom is `0.9397x` stock CPU.

## v18r2 Acceptance Decision

- Accepted v17 baseline: best custom decode `1.93417` TPS, TPOT `517.018 ms`.
- New v18r2 full Device Farm custom result: decode `2.14021` TPS, TPOT `467.244 ms`.
- Delta: `+10.65%` decode TPS and `-49.774 ms` TPOT versus v17 best custom.
- Acceptance rule result: ACCEPTED. The run passed host correctness tests, Android build, full Qwen3.5-9B Device Farm execution, and full-custom guardrails.
- The first v18 run `customlib_cpu_vulkan_hybrid_v18_optimization_attempt` failed before benchmark because the test spec used Device Farm PUT upload URLs as device GET download URLs. It produced no `BENCH_RESULT_JSON` and is not counted as a performance result. v18r2 fixed the test spec to use `get-upload` downloadable URLs.

## Device Farm Evidence

- Project ARN: `arn:aws:devicefarm:us-west-2:884244642857:project:64d2cc31-abd6-49f8-97da-162f82410bc0`
- Device pool ARN: `arn:aws:devicefarm:us-west-2:884244642857:devicepool:64d2cc31-abd6-49f8-97da-162f82410bc0/14d31c96-b8fc-4930-99c7-1a8948124213`
- Device: Samsung Galaxy S26 Ultra, model ID SM-S948U1, Android 16.
- Model: `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, W4A16 groupwise quantization, group size 64.
- Full model zip SHA-256 verified on-device: `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`.
- Split package bytes: 4,500,000,000 + 4,500,000,000 + 2,266,405,198 = 11,266,405,198.
- Split SHA-256 values: `3b13bdc4a158b6745f58cfe0dc4c31e485990a50f24d8f14809f5df0e2aa15dc`, `60b8c1d898e4db8b626f750660174f20c05a7e28a43ca11192d58494c3e9211f`, `32d8becc5a77be798a9bc8a3c26509e419942b57aad59f8d4b55310de7248b18`.
- Presentation deck: `results/reports/qwen35_9b_v18r2_optimization_presentation.pptx`; visual QA contact sheet: `results/reports/qwen35_9b_v18r2_optimization_presentation_contact_sheet.png`.

| Run | Device Farm run ARN | Result | Evidence |
| --- | --- | --- | --- |
| stock_mnn_cpu_v17_backend_sweep | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7e44236c-db1a-4900-9fd8-7d8d7d654e28` | PASSED | `results/reports/evidence/stock_mnn_cpu_benchmark_v17.json` |
| stock_mnn_vulkan_v17_backend_sweep | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/067c195b-1e14-4bca-998d-c7d38a65c5c7` | PASSED by harness, benchmark process crashed | `results/reports/evidence/stock_mnn_vulkan_benchmark_failure_v17.json` |
| customlib_cpu_v17_backend_sweep | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/8d765268-aacd-4f52-b845-f5370b4d522f` | PASSED | `results/reports/evidence/customlib_cpu_benchmark_v17.json` |
| customlib_cpu_vulkan_hybrid_v17_backend_sweep | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1de54984-c9d9-41d1-81c1-7eed941585ed` | PASSED, accepted v17 baseline | `results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v17.json` |
| customlib_cpu_vulkan_hybrid_v18_optimization_attempt | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/f691220e-185e-4a4e-907f-dae49765db9a` | FAILED before benchmark: model download 403 from non-download upload URL | raw artifact only, not a performance result |
| customlib_cpu_vulkan_hybrid_v18r2_optimization_attempt | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1b18e97c-38fe-4581-97c8-b7688b5fbc91` | PASSED, official optimized final custom result | `results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v18r2.json` |

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

## Backend Sweep And Final Comparison

| Variant | Requested backend | Actual backend | Status | Prefill TPS mean | Decode TPS mean | Decode TPOT mean | Device minutes total |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| Stock MNN | cpu | cpu | ok | 45.6380 | 2.27746 | 439.086 ms | 25.35 |
| Stock MNN | vulkan | unavailable | process crashed before `BENCH_RESULT_JSON` | n/a | n/a | n/a | 18.05 |
| Customlib v17 best | cpu_vulkan_hybrid | cpu | ok, accepted baseline | 2.21477 | 1.93417 | 517.018 ms | 41.80 |
| Customlib v18r2 optimized | cpu_vulkan_hybrid | cpu | ok, official final custom result | 2.44242 | 2.14021 | 467.244 ms | 39.69 |

Stock Vulkan evidence: the instrumentation output records `BENCH_START engine=mnn_stock ... backend=vulkan`, Adreno Vulkan driver initialization, `Application Name: MNN_Vulkan`, then MNN cache/backend messages followed by `INSTRUMENTATION_RESULT: shortMsg=Process crashed.` No Vulkan TPS/TPOT is reported because no benchmark JSON was produced.

Custom Vulkan evidence: the optimized custom JSON reports `custom_backend_requested = cpu_vulkan_hybrid`, `custom_backend_actual = cpu`, `vulkan_attempt.status = ok`, `libvulkan_loaded = true`, `vkGetInstanceProcAddr_found = true`, `full_or_hybrid_kernel_status = not_enabled_in_this_build`, and `custom_path.vulkan_generation_kernels_used = false`.

Optional OpenCL, NNAPI, and QNN variants were not run in the final accepted sweep and are not claimed.

## Overall Comparisons

| Comparison | Decode TPS ratio | Interpretation |
| --- | ---: | --- |
| Custom v18r2 / Stock CPU | 0.9397x | Optimized custom is still slower than stock CPU by 6.03% in decode TPS. |
| Custom v18r2 / Custom v17 best | 1.1065x | v18r2 improves the accepted custom baseline by 10.65% decode TPS. |
| Stock Vulkan / Custom hybrid | n/a | Stock Vulkan crashed before metrics; custom hybrid did not execute Vulkan kernels. |
| Best custom / Best stock | 0.9397x | No custom speedup is claimed. |

## Custom Path Coverage

Measured custom generation evidence from the v18r2 JSON:

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
| Stock MNN | cpu | 0 | true | 12,855.747 | 112,843.695 | 39.82650 | 2.26862 |
| Stock MNN | cpu | 1 | false | 11,194.592 | 112,057.582 | 45.73640 | 2.28454 |
| Stock MNN | cpu | 2 | false | 11,231.535 | 113,070.093 | 45.58590 | 2.26408 |
| Stock MNN | cpu | 3 | false | 11,230.103 | 112,095.991 | 45.59170 | 2.28376 |
| Customlib v17 best | cpu_vulkan_hybrid | 0 | true | 189,802.000 | 125,560.000 | 2.69754 | 2.03886 |
| Customlib v17 best | cpu_vulkan_hybrid | 1 | false | 232,799.000 | 133,033.000 | 2.19932 | 1.92434 |
| Customlib v17 best | cpu_vulkan_hybrid | 2 | false | 231,519.000 | 133,006.000 | 2.21148 | 1.92473 |
| Customlib v17 best | cpu_vulkan_hybrid | 3 | false | 229,236.000 | 131,051.000 | 2.23351 | 1.95344 |
| Customlib v18r2 | cpu_vulkan_hybrid | 0 | true | 178,721.000 | 114,228.000 | 2.86480 | 2.24112 |
| Customlib v18r2 | cpu_vulkan_hybrid | 1 | false | 210,709.000 | 120,130.000 | 2.42989 | 2.13102 |
| Customlib v18r2 | cpu_vulkan_hybrid | 2 | false | 209,307.000 | 119,271.000 | 2.44616 | 2.14637 |
| Customlib v18r2 | cpu_vulkan_hybrid | 3 | false | 208,878.000 | 119,446.000 | 2.45120 | 2.14323 |

## Custom Per-Kernel Wall Clock

This table uses the official optimized custom evidence file, `customlib_cpu_vulkan_hybrid_benchmark_v18r2.json`. The requested backend was `cpu_vulkan_hybrid`, but the actual backend for every measured custom op was CPU.

| Kernel / op family | Op family | Backend | Calls | Total ms | Mean ms | Min ms | Max ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| prefill_token_custom | other | cpu | 512 | 208,875.000 | 407.959000 | 371.975000 | 446.606000 |
| linear_down_proj_w4a16 | down_proj | cpu | 24,576 | 61,982.800 | 2.522080 | 2.322860 | 4.435780 |
| linear_up_proj_w4a16 | up_proj | cpu | 24,576 | 61,703.400 | 2.510720 | 2.260420 | 5.364480 |
| linear_gate_proj_w4a16 | gate_proj | cpu | 24,576 | 61,620.800 | 2.507360 | 2.202760 | 5.236090 |
| linear_attn_in_proj_qkv_w4a16 | linear_attention_projection | cpu | 18,432 | 31,048.800 | 1.684500 | 1.527710 | 4.220830 |
| linear_attention_state_update_custom | linear_attention_state | cpu | 18,432 | 30,243.800 | 1.640830 | 1.506250 | 2.974110 |
| linear_attn_out_proj_w4a16 | linear_attention_projection | cpu | 18,432 | 15,868.600 | 0.860925 | 0.794739 | 2.234840 |
| linear_attn_in_proj_z_w4a16 | linear_attention_projection | cpu | 18,432 | 15,791.000 | 0.856715 | 0.792396 | 1.848230 |
| sampling_greedy_custom | sampling | cpu | 256 | 11,971.300 | 46.762800 | 43.378600 | 56.150400 |
| lm_head_custom | lm_head | cpu | 256 | 11,971.000 | 46.761800 | 43.378200 | 56.147600 |
| linear_q_proj_w4a16 | q_proj | cpu | 6,144 | 10,345.300 | 1.683800 | 1.533910 | 2.878070 |
| attention_score_custom | attention_score | cpu | 6,144 | 10,330.400 | 1.681380 | 0.003906 | 4.637240 |
| linear_o_proj_w4a16 | o_proj | cpu | 6,144 | 5,265.010 | 0.856935 | 0.794167 | 1.851980 |
| attention_v_reduce_custom | attention_v_reduce | cpu | 6,144 | 2,458.690 | 0.400177 | 0.001250 | 1.659220 |
| linear_k_proj_w4a16 | k_proj | cpu | 6,144 | 1,845.410 | 0.300360 | 0.275938 | 1.199270 |
| linear_v_proj_w4a16 | v_proj | cpu | 6,144 | 1,839.090 | 0.299332 | 0.275677 | 1.049370 |
| linear_attention_conv1d_custom | linear_attention_state | cpu | 18,432 | 1,808.000 | 0.098090 | 0.090781 | 0.217604 |
| silu_gate_mul_custom | activation | cpu | 24,576 | 1,364.420 | 0.055518 | 0.050729 | 0.188281 |
| linear_attn_in_proj_a_w4a16 | linear_attention_projection | cpu | 18,432 | 660.087 | 0.035812 | 0.033125 | 0.339896 |
| linear_attn_in_proj_b_w4a16 | linear_attention_projection | cpu | 18,432 | 653.334 | 0.035446 | 0.032916 | 0.091459 |
| linear_attention_gated_rmsnorm_custom | linear_attention_state | cpu | 18,432 | 430.918 | 0.023379 | 0.021406 | 0.188125 |
| attention_output_gate_custom | attention | cpu | 6,144 | 190.972 | 0.031083 | 0.025364 | 0.110469 |
| attention_softmax_custom | attention_softmax | cpu | 6,144 | 167.327 | 0.027234 | 0.000260 | 0.161562 |
| rmsnorm_input | rmsnorm | cpu | 24,576 | 147.290 | 0.005993 | 0.005260 | 0.038437 |
| rmsnorm_post_attention | rmsnorm | cpu | 24,576 | 146.023 | 0.005942 | 0.005312 | 0.070833 |
| rope_qk_custom | rope | cpu | 6,144 | 134.359 | 0.021868 | 0.014531 | 0.062865 |
| linear_attention_qk_l2norm_custom | linear_attention_state | cpu | 18,432 | 99.569 | 0.005402 | 0.004896 | 0.079688 |
| embedding_bf16_row_read | other | cpu | 768 | 21.716 | 0.028276 | 0.021250 | 0.111146 |
| prefill_kv_build_custom | other | cpu | 6,144 | 14.639 | 0.002383 | 0.001250 | 0.025469 |
| kv_append_custom | other | cpu | 6,144 | 12.357 | 0.002011 | 0.001041 | 0.025156 |
| rmsnorm_final | rmsnorm | cpu | 768 | 4.803 | 0.006254 | 0.005573 | 0.016719 |

Note: `sampling_greedy_custom` wraps the greedy section and therefore overlaps with `lm_head_custom`; it should not be summed independently with `lm_head_custom` as exclusive time.

## Generated Kernel Microbench

The microbench ran on the same custom Device Farm APK after measured custom generation completed. It is not used for the overall TPS calculation.

| Kernel | Backend | Implementation | Qwen3.5 shape | Mean wall ms | Median wall ms |
| --- | --- | --- | --- | ---: | ---: |
| gemv_w4a16_attn_4096x4096 | cpu | generated_tiled_neon_fused_dequant_gemv_parallel_group_sum_reuse | attention_or_output_projection | 0.943090 | 0.940365 |
| gemv_w4a16_mlp_up_12288x4096 | cpu | generated_tiled_neon_fused_dequant_gemv_parallel_group_sum_reuse | mlp_gate_or_up_projection | 2.823020 | 2.998070 |
| gemv_w4a16_mlp_down_4096x12288 | cpu | generated_tiled_neon_fused_dequant_gemv_parallel_group_sum_reuse | mlp_down_projection | 2.763470 | 2.720210 |
| rmsnorm_hidden4096 | cpu | customlib_reference | hidden_size | 0.005573 | 0.005573 |
| rope_q_heads16_dim256_pos512 | cpu | customlib_reference | q_heads_x_head_dim | 0.124202 | 0.124011 |
| gqa_decode_ctx512_q16_kv4_dim256 | cpu | customlib_reference | full_attention_layer_decode | 2.121770 | 2.124530 |
| gated_delta_decode_k128_v128 | cpu | customlib_reference | linear_attention_layer_decode | 0.048368 | 0.041927 |

## MNN Hot-Path Trace: Top Op Types

The MNN hot-path trace is a separate debug-callback trace collected inside the custom APK after measured custom generation. It is evidence for MNN op wall-clock hotspots; it is not part of the measured custom generation path.

| Stage | Type | Calls | Total ms | Mean ms |
| --- | --- | ---: | ---: | ---: |
| prefill_or_first_token_inferred | Convolution | 249 | 10,381.000 | 41.691000 |
| decode_inferred | Convolution | 3,984 | 4,357.200 | 1.093680 |
| decode_inferred | UnaryOp | 2,464 | 1,344.130 | 0.545508 |
| prefill_or_first_token_inferred | Raster | 521 | 490.440 | 0.941343 |
| decode_inferred | LinearAttention | 384 | 446.996 | 1.164050 |
| decode_inferred | LayerNorm | 1,680 | 357.306 | 0.212682 |
| prefill_or_first_token_inferred | LinearAttention | 24 | 327.354 | 13.639700 |
| decode_inferred | While | 528 | 276.481 | 0.523639 |
| prefill_or_first_token_inferred | UnaryOp | 154 | 244.370 | 1.586820 |
| prefill_or_first_token_inferred | Attention | 8 | 119.113 | 14.889100 |
| prefill_or_first_token_inferred | BinaryOp | 169 | 118.611 | 0.701838 |
| decode_inferred | Attention | 128 | 96.900 | 0.757034 |

## MNN Hot-Path Trace: Top Op Names

| Stage | Type | Name | Calls | Total ms | Mean ms |
| --- | --- | --- | ---: | ---: | ---: |
| decode_inferred | Convolution | `/lm/lm_head/Linear` | 16 | 244.521 | 15.282500 |
| prefill_or_first_token_inferred | Convolution | `/layers.24/mlp/down_proj/Linear` | 1 | 96.471 | 96.470500 |
| prefill_or_first_token_inferred | Convolution | `/layers.22/mlp/down_proj/Linear` | 1 | 94.328 | 94.327700 |
| prefill_or_first_token_inferred | Convolution | `/layers.19/mlp/down_proj/Linear` | 1 | 93.707 | 93.707400 |
| prefill_or_first_token_inferred | Convolution | `/layers.27/mlp/down_proj/Linear` | 1 | 93.021 | 93.020600 |
| prefill_or_first_token_inferred | Convolution | `/layers.18/mlp/down_proj/Linear` | 1 | 92.993 | 92.992500 |
| prefill_or_first_token_inferred | Convolution | `/layers.31/mlp/down_proj/Linear` | 1 | 92.864 | 92.864200 |
| prefill_or_first_token_inferred | Convolution | `/layers.20/mlp/gate_proj/Linear` | 1 | 91.437 | 91.437200 |
| prefill_or_first_token_inferred | Convolution | `/layers.19/mlp/up_proj/Linear` | 1 | 91.177 | 91.176600 |
| prefill_or_first_token_inferred | Convolution | `/layers.7/mlp/down_proj/Linear` | 1 | 89.399 | 89.398900 |
| prefill_or_first_token_inferred | Convolution | `/layers.25/mlp/down_proj/Linear` | 1 | 88.985 | 88.984700 |
| prefill_or_first_token_inferred | Convolution | `/layers.29/mlp/gate_proj/Linear` | 1 | 88.893 | 88.893000 |

## v18r2 Optimization Changes

- Kept the same custom math path and full-custom selected kernels, then reduced allocation and file-I/O overhead around decode/prefill.
- Opened `embeddings_bf16.bin` once in the runtime loader and reused a BF16 row buffer instead of opening/allocating per token.
- Reserved full-attention KV cache capacity after reset for the known prompt plus decode length budget.
- Reused attention score/max scratch buffers and FFN buffers instead of per-token vector allocation/clearing.
- Changed append paths to reserve-aware resize/copy without changing tensor semantics.

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

- Host v18r2: `ctest --test-dir build-host-opt --output-on-failure` -> 2/2 passed (`xq_kernel_correctness`, `xq_runtime_correctness`).
- Android v18r2 build: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_android.ps1` completed and produced the custom debug APK plus androidTest APK used in the v18r2 Device Farm run.
- Device Farm stock CPU v17: PASSED and emitted benchmark JSON.
- Device Farm stock Vulkan v17: process crashed after Vulkan initialization; failure evidence retained.
- Device Farm custom v18r2: PASSED and emitted benchmark JSON; actual measured generation backend was CPU.
- Presentation QA: `slides_test.py results/reports/qwen35_9b_v18r2_optimization_presentation.pptx` -> passed, no overflow detected.

## Cleanup Evidence

The repo ignores generated build trees, Android build outputs, raw Device Farm downloads, APK/AAB/SO/ZIP/BIN/MNN/XPACK/SAFETENSORS artifacts, virtualenvs, and model directories. `scripts/cleanup_local_artifacts.ps1` and `scripts/cleanup_local_artifacts.sh` remove local raw/build/temp artifacts while preserving source, reports, and small evidence files.

## Final Conclusion

The final custom benchmark is a measured full custom prefill/decode path with no listed fallback families and no measured `MNN::Llm::response` call. Requirement 1 and Requirement 2 are satisfied with v18r2 Device Farm evidence. v18r2 materially improves the custom library over v17, but it is still slower than stock MNN CPU on the Samsung Galaxy S26 Ultra, so the correct final performance verdict is no speedup claimed.

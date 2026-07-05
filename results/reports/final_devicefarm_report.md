# Final Device Farm Report: Qwen3.5-9B Stock MNN vs Full Custom Decode v16

## Honest Verdict

- Faithful benchmark: YES. Stock MNN and customlib both ran on AWS Device Farm on the Samsung Galaxy S26 Ultra pool with the same Qwen3.5-9B package, same prompt length, same max_new_tokens, same greedy settings, and same warmup/measured count.
- Requirement 1 met: YES. The final code walkthrough is `docs/kernel_library_code_walkthrough_final.md` and covers the kernel library architecture, generated kernels, MNN/fallback connectors, JNI connector, benchmark connector, and Device Farm connector.
- Requirement 2 met: YES. This report includes stock/custom TPOT/TPS, custom per-kernel wall-clock rows, MNN hot-path trace top op type/name wall-clock rows, and Device Farm run evidence.
- Custom speedup claim allowed: NO. Custom decode TPS is 0.1859x stock decode TPS; stock MNN is 5.38x faster on decode TPS. The result is a complete custom-path correctness/coverage delivery, not a speedup.

## Device Farm Evidence

- Project ARN: `arn:aws:devicefarm:us-west-2:884244642857:project:64d2cc31-abd6-49f8-97da-162f82410bc0`
- Device: Samsung Galaxy S26 Ultra, model ID SM-S948U1, Android 16.
- Device ARN: `arn:aws:devicefarm:us-west-2::device:536B9FDAEAA14A11B504A3ECC86DA717`
- Device pool ARN: `arn:aws:devicefarm:us-west-2:884244642857:devicepool:64d2cc31-abd6-49f8-97da-162f82410bc0/14d31c96-b8fc-4930-99c7-1a8948124213`
- Stock MNN run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/baed9f8e-2a52-4b93-8584-60c305b73757`; result PASSED; counters 3/3 passed; device minutes total 26.01.
- Customlib run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7bc0f1d8-7640-4574-8309-da6bdb9fa642`; result PASSED; counters 3/3 passed; device minutes total 129.34.
- Stock instrumentation output: `results/raw/devicefarm_stock_v16_final_measured3/expanded_07/Host_Machine_Files/$DEVICEFARM_LOG_DIR/instrumentation_output.txt`, `OK (1 test)`, time 1,522.924 s.
- Custom instrumentation output: `results/raw/devicefarm_custom_v16_final_measured3/expanded_07/Host_Machine_Files/$DEVICEFARM_LOG_DIR/instrumentation_output.txt`, `OK (1 test)`, time 7,722.587 s.
- Presentation deck: `results/reports/qwen35_9b_full_custom_v16_presentation.pptx`.
- Model package: Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, W4A16 groupwise quantization, group size 64.
- Model split package bytes: 4,500,000,000 + 4,500,000,000 + 2,266,405,198 = 11,266,405,198.
- Full model zip SHA-256 verified on-device: `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`.
- Bootstrap evidence: both `model_bootstrap_discovery.txt` files show 3 model parts downloaded, reassembled, SHA-256 checked, unzipped, and `source=downloaded`.

## Same-Settings Comparison

| Field | Stock MNN | Customlib |
| --- | ---: | ---: |
| Prompt tokens requested | 512 | 512 |
| max_new_tokens | 256 | 256 |
| Prompt token id | 16 | 16 |
| Temperature / top_k / top_p | 0 / 1 / 1 | 0 / 1 / 1 |
| Warmup / measured iterations | 1 / 3 | 1 / 3 |
| Backend | cpu | cpu |
| Quantization | W4A16 groupwise, group 64 | W4A16 groupwise, group 64 |

| Metric | Stock MNN mean | Customlib mean | Custom / Stock |
| --- | ---: | ---: | ---: |
| Prefill TPS | 45.0960 | 0.486717 | 0.0108x |
| Decode TPS | 2.28587 | 0.424895 | 0.1859x |
| Decode TPOT ms | 437.470 | 2,353.52 | 5.38x stock TPOT |

## Custom Path Coverage

Measured custom generation evidence from `customlib_benchmark.json`:

```text
custom_decode_loop;hotpath_replaced=true;full_custom_decode=true;linear=q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj,linear_attn_qkv_a_b_z_out,lm_head;rmsnorm=custom;rope=custom;attention=custom_gqa_decode;linear_attention_state=custom_gated_delta;sampling=custom_greedy;prefill_kv_build=custom;fallback_ops=none
```

- `runtime.selected_kernels.hotpath_replaced = true`
- `runtime.selected_kernels.full_custom_decode = true`
- `runtime.selected_kernels.fallback_op_families = []`
- `custom_path.use_mnn_fallback = 0`
- `custom_path.calls_mnn_llm_response_for_measured_generation = false`

| Op family | Measured path | Fallback? |
| --- | ---: | ---: |
| q_proj | custom | no |
| k_proj | custom | no |
| v_proj | custom | no |
| o_proj | custom | no |
| gate_proj | custom | no |
| up_proj | custom | no |
| down_proj | custom | no |
| rmsnorm | custom | no |
| rope | custom | no |
| attention | custom | no |
| linear_attention_state | custom | no |
| lm_head | custom | no |
| sampling | custom | no |
| prefill_kv_build | custom | no |

## Overall Runs

| Engine | Run | Warmup | Prefill ms | Decode ms | Prefill TPS | Decode TPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Stock MNN | 0 | true | 12,781.386 | 112,600.067 | 40.0583 | 2.27353 |
| Stock MNN | 1 | false | 11,382.537 | 111,288.924 | 44.9812 | 2.30032 |
| Stock MNN | 2 | false | 11,362.384 | 112,847.525 | 45.0610 | 2.26855 |
| Stock MNN | 3 | false | 11,315.938 | 111,851.634 | 45.2459 | 2.28875 |
| Customlib | 0 | true | 1,049,430.000 | 616,579.000 | 0.487883 | 0.415194 |
| Customlib | 1 | false | 1,064,410.000 | 601,313.000 | 0.481018 | 0.425735 |
| Customlib | 2 | false | 1,049,220.000 | 607,101.000 | 0.487981 | 0.421676 |
| Customlib | 3 | false | 1,042,450.000 | 599,148.000 | 0.491151 | 0.427274 |

## Custom Per-Kernel Wall Clock

| Kernel / op family | Calls | Total ms | Mean ms | Min ms | Max ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| prefill_token_custom | 512 | 1,042,450.000 | 2,036.030000 | 1,969.150000 | 2,109.740000 |
| linear_up_proj_w4a16 | 24576 | 360,780.000 | 14.680200 | 13.976900 | 21.602600 |
| linear_gate_proj_w4a16 | 24576 | 360,698.000 | 14.676900 | 13.963500 | 22.237700 |
| linear_down_proj_w4a16 | 24576 | 338,658.000 | 13.780000 | 13.246400 | 21.086200 |
| linear_attn_in_proj_qkv_w4a16 | 18432 | 180,403.000 | 9.787480 | 9.315880 | 13.900400 |
| linear_attn_in_proj_z_w4a16 | 18432 | 90,195.900 | 4.893440 | 4.649430 | 7.988750 |
| linear_attn_out_proj_w4a16 | 18432 | 89,625.600 | 4.862500 | 4.615210 | 7.746770 |
| lm_head_custom | 256 | 75,668.800 | 295.581000 | 285.727000 | 325.913000 |
| linear_q_proj_w4a16 | 6144 | 60,117.500 | 9.784750 | 9.309640 | 16.971100 |
| linear_o_proj_w4a16 | 6144 | 29,996.600 | 4.882260 | 4.681300 | 6.301560 |
| linear_attention_state_update_custom | 18432 | 24,343.700 | 1.320730 | 1.253330 | 2.134630 |
| attention_score_custom | 6144 | 8,454.720 | 1.376090 | 0.003386 | 3.423590 |
| linear_k_proj_w4a16 | 6144 | 7,518.140 | 1.223660 | 1.161410 | 1.946350 |
| linear_v_proj_w4a16 | 6144 | 7,517.260 | 1.223510 | 1.162030 | 1.959270 |
| attention_v_reduce_custom | 6144 | 2,082.440 | 0.338938 | 0.000937 | 1.171930 |
| linear_attention_conv1d_custom | 18432 | 1,462.490 | 0.079345 | 0.075573 | 0.251302 |
| silu_gate_mul_custom | 24576 | 1,120.840 | 0.045607 | 0.042864 | 0.359271 |
| linear_attn_in_proj_a_w4a16 | 18432 | 698.775 | 0.037911 | 0.035833 | 0.288281 |
| linear_attn_in_proj_b_w4a16 | 18432 | 694.651 | 0.037687 | 0.035521 | 0.229948 |
| linear_attention_gated_rmsnorm_custom | 18432 | 348.294 | 0.018896 | 0.017864 | 0.132917 |
| attention_output_gate_custom | 6144 | 155.353 | 0.025285 | 0.021719 | 0.142083 |
| attention_softmax_custom | 6144 | 136.319 | 0.022187 | 0.000312 | 0.110833 |
| rmsnorm_input | 24576 | 121.801 | 0.004956 | 0.004322 | 0.106875 |
| rmsnorm_post_attention | 24576 | 120.707 | 0.004912 | 0.004375 | 0.037917 |
| rope_qk_custom | 6144 | 108.406 | 0.017644 | 0.013021 | 0.105469 |
| linear_attention_qk_l2norm_custom | 18432 | 84.492 | 0.004584 | 0.004114 | 0.050000 |
| embedding_bf16_row_read | 768 | 80.655 | 0.105020 | 0.069427 | 0.245625 |
| sampling_greedy_custom | 256 | 79.388 | 0.310111 | 0.301042 | 0.463750 |
| prefill_kv_build_custom | 6144 | 14.738 | 0.002399 | 0.001562 | 0.019531 |
| kv_append_custom | 6144 | 10.785 | 0.001755 | 0.000937 | 0.018489 |
| rmsnorm_final | 768 | 4.044 | 0.005266 | 0.004635 | 0.019011 |

## Generated Kernel Microbench

The microbench was run on the same custom Device Farm APK after measured custom generation completed. It is not used for the overall TPS calculation.

| Kernel | Implementation | Shape | Mean wall ms | Median wall ms |
| --- | ---: | ---: | ---: | ---: |
| gemv_w4a16_attn_4096x4096 | generated_tiled_neon_fused_dequant_gemv | attention_or_output_projection | 4.539 | 4.534 |
| gemv_w4a16_mlp_up_12288x4096 | generated_tiled_neon_fused_dequant_gemv | mlp_gate_or_up_projection | 13.977 | 13.975 |
| gemv_w4a16_mlp_down_4096x12288 | generated_tiled_neon_fused_dequant_gemv | mlp_down_projection | 13.470 | 13.475 |
| rmsnorm_hidden4096 | customlib_reference | hidden_size | 0.006 | 0.006 |
| rope_q_heads16_dim256_pos512 | customlib_reference | q_heads_x_head_dim | 0.125 | 0.125 |
| gqa_decode_ctx512_q16_kv4_dim256 | customlib_reference | full_attention_layer_decode | 2.136 | 2.132 |
| gated_delta_decode_k128_v128 | customlib_reference | linear_attention_layer_decode | 0.042 | 0.042 |

## MNN Hot-Path Trace: Top Op Types

The MNN hot-path trace is a separate debug-callback trace inside the custom APK after measured custom generation. It is evidence for stock MNN op wall-clock hotspots; it is not part of the measured custom generation path.

| Stage | Type | Calls | Total ms | Mean ms |
| --- | ---: | ---: | ---: | ---: |
| prefill_or_first_token_inferred | Convolution | 249 | 15,431.900 | 61.975400 |
| decode_inferred | Convolution | 3984 | 4,262.680 | 1.069950 |
| decode_inferred | UnaryOp | 2464 | 1,329.820 | 0.539700 |
| prefill_or_first_token_inferred | Raster | 521 | 514.922 | 0.988334 |
| decode_inferred | LinearAttention | 384 | 444.280 | 1.156980 |
| decode_inferred | LayerNorm | 1680 | 351.638 | 0.209308 |
| prefill_or_first_token_inferred | LinearAttention | 24 | 350.422 | 14.600900 |
| decode_inferred | While | 528 | 274.113 | 0.519154 |
| prefill_or_first_token_inferred | UnaryOp | 154 | 256.648 | 1.666550 |
| prefill_or_first_token_inferred | BinaryOp | 169 | 123.294 | 0.729550 |
| prefill_or_first_token_inferred | Attention | 8 | 118.938 | 14.867200 |
| prefill_or_first_token_inferred | LayerNorm | 105 | 114.050 | 1.086190 |
| decode_inferred | Attention | 128 | 94.394 | 0.737454 |
| decode_inferred | Raster | 8336 | 53.541 | 0.006423 |
| prefill_or_first_token_inferred | While | 81 | 44.071 | 0.544089 |
| decode_inferred | BinaryOp | 3472 | 14.314 | 0.004123 |
| prefill_or_first_token_inferred | Cast | 25 | 11.194 | 0.447779 |
| decode_inferred | Cast | 400 | 1.697 | 0.004243 |

## MNN Hot-Path Trace: Top Op Names

| Stage | Type | Name | Calls | Total ms | Mean ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| decode_inferred | Convolution | `/lm/lm_head/Linear` | 16 | 248.948 | 15.559300 |
| prefill_or_first_token_inferred | Convolution | `/layers.21/mlp/down_proj/Linear` | 1 | 133.669 | 133.669000 |
| prefill_or_first_token_inferred | Convolution | `/layers.20/mlp/down_proj/Linear` | 1 | 131.440 | 131.440000 |
| prefill_or_first_token_inferred | Convolution | `/layers.26/mlp/down_proj/Linear` | 1 | 131.103 | 131.103000 |
| prefill_or_first_token_inferred | Convolution | `/layers.23/mlp/down_proj/Linear` | 1 | 130.492 | 130.492000 |
| prefill_or_first_token_inferred | Convolution | `/layers.22/mlp/up_proj/Linear` | 1 | 127.624 | 127.624000 |
| prefill_or_first_token_inferred | Convolution | `/layers.23/mlp/gate_proj/Linear` | 1 | 127.352 | 127.352000 |
| prefill_or_first_token_inferred | Convolution | `/layers.25/mlp/down_proj/Linear` | 1 | 126.534 | 126.534000 |
| prefill_or_first_token_inferred | Convolution | `/layers.18/mlp/down_proj/Linear` | 1 | 126.410 | 126.410000 |
| prefill_or_first_token_inferred | Convolution | `/layers.16/mlp/down_proj/Linear` | 1 | 123.756 | 123.756000 |
| prefill_or_first_token_inferred | Convolution | `/layers.13/mlp/down_proj/Linear` | 1 | 123.575 | 123.575000 |
| prefill_or_first_token_inferred | Convolution | `/layers.27/mlp/gate_proj/Linear` | 1 | 123.413 | 123.413000 |
| prefill_or_first_token_inferred | Convolution | `/layers.27/mlp/up_proj/Linear` | 1 | 122.745 | 122.745000 |
| prefill_or_first_token_inferred | Convolution | `/layers.25/mlp/up_proj/Linear` | 1 | 122.729 | 122.729000 |
| prefill_or_first_token_inferred | Convolution | `/layers.30/mlp/gate_proj/Linear` | 1 | 122.404 | 122.404000 |
| prefill_or_first_token_inferred | Convolution | `/layers.24/mlp/up_proj/Linear` | 1 | 122.400 | 122.400000 |
| prefill_or_first_token_inferred | Convolution | `/layers.14/mlp/down_proj/Linear` | 1 | 121.655 | 121.655000 |
| prefill_or_first_token_inferred | Convolution | `/layers.8/mlp/down_proj/Linear` | 1 | 121.591 | 121.591000 |
| prefill_or_first_token_inferred | Convolution | `/layers.25/mlp/gate_proj/Linear` | 1 | 121.285 | 121.285000 |
| prefill_or_first_token_inferred | Convolution | `/layers.20/mlp/up_proj/Linear` | 1 | 120.946 | 120.946000 |

## Code Walkthrough Pointers

- Public ABI: `customlib/include/xqwen35.h`.
- Custom runtime selection: `customlib/runtime/session.cpp` creates `CustomModel` when `use_mnn_fallback = 0`; the Android custom benchmark sets that field to zero.
- Full custom prefill/decode: `customlib/runtime/custom_model.cpp` implements prompt-token prefill, KV append, grouped-query attention, gated-delta linear attention state, final `lm_head_custom`, and greedy sampling.
- Generated W4A16 GEMV: `customlib/kernels/generated/arm64_neon/xq_gemv_w4a16_neon.cpp` uses tiled rows and NEON fused int4 unpack/dequant dot groups. The W4 file contains no `gemvLowBitReference` call.
- Packer/exporter: `customlib/packer/pack_qwen35_xq4.py` exports `lm_head.weight`, full-attention projections, MLP projections, linear-attention `in_proj_a`, `in_proj_b`, `conv1d.weight`, `A_log`, and `dt_bias`.
- Stock MNN connector: `android/app/src/main/cpp/stock_benchmark_jni.cpp`.
- Custom JNI/benchmark connector: `android/benchmark_app/src/main/cpp/benchmark_jni.cpp`.
- Device Farm bootstrap connector: `android/benchmark_app/src/androidTest/java/com/example/xqwen35bench/ModelBootstrap.java`.

## Test Evidence

- Host: `C:\msys64\ucrt64\bin\ctest.exe --test-dir build-host --output-on-failure` -> 2/2 passed (`xq_kernel_correctness`, `xq_runtime_correctness`).
- Android build: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_android.ps1` completed and produced stock/custom debug APKs plus androidTest APKs used in v16 Device Farm runs.
- Device Farm stock v16: PASSED, 3/3 counters, `OK (1 test)`.
- Device Farm custom v16: PASSED, 3/3 counters, `OK (1 test)`.

## Final Conclusion

The final custom benchmark is a measured full custom prefill/decode path with no listed fallback families and no measured `MNN::Llm::response` call. It satisfies the kernel-library walkthrough and stock-vs-custom comparison requirements. The custom path is slower than stock MNN on this CPU benchmark, so the correct conclusion is functional full-custom coverage, not a performance win.

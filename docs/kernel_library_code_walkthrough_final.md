# Kernel Library Code Walkthrough Final

This document describes the final v16 custom inference library used for the Qwen3.5-9B AWS Device Farm comparison. It is written to match the measured code path and the final `BENCH_RESULT_JSON` evidence, not a planned architecture.

## Final Measured Path

The final custom Android benchmark sets `xq_options.use_mnn_fallback = 0` in `android/benchmark_app/src/main/cpp/benchmark_jni.cpp` and enters the public ABI in `customlib/include/xqwen35.h`.

The measured custom generation path is:

```text
NativeBenchmark.runBenchmark
  -> xq_create
  -> xq_generate
     -> xq::runtime::Session::prefill
        -> xq::runtime::CustomModel::prefill
           -> load embedding for every prompt token
           -> run full layer stack for each prompt position
           -> append full-attention K/V cache
           -> update linear-attention recurrent state
     -> xq::runtime::Session::decodeOne
        -> xq::runtime::CustomModel::decodeOne
           -> run custom layer stack
           -> run custom lm_head
           -> run greedy sampling
```

For the measured custom run:

- `custom_path.use_mnn_fallback = 0`
- `custom_path.calls_mnn_llm_response_for_measured_generation = false`
- `runtime.selected_kernels.full_custom_decode = true`
- `runtime.selected_kernels.hotpath_replaced = true`
- `runtime.selected_kernels.fallback_op_families = []`

The optional MNN fallback connector still exists for API compatibility, but it is not used by the measured custom benchmark.

## Repository Architecture

| Area | Files | Role |
| --- | --- | --- |
| Public ABI | `customlib/include/xqwen35.h` | Stable C ABI for Android/JNI and host tests. |
| Session connector | `customlib/runtime/session.cpp` | Chooses MNN fallback only when requested; final custom run loads `CustomModel`. |
| Custom runtime | `customlib/runtime/custom_model.cpp` | Implements prefill, decode, attention, linear attention, lm_head, sampling, and trace recording. |
| Generated kernels | `customlib/kernels/generated/arm64_neon/xq_gemv_w4a16_neon.cpp` | Fused dequant + GEMV W4A16 kernel used by decode linear families. |
| Reference kernels | `customlib/kernels/reference/*.cpp` | Host correctness references and non-final low-bit experiments. |
| Packer | `customlib/packer/pack_qwen35_xq4.py` | Converts Qwen3.5 safetensors into the custom W4A16 package and manifest. |
| Stock Android app | `android/app` | Stock MNN baseline instrumentation. |
| Custom Android app | `android/benchmark_app` | Customlib instrumentation, JSON evidence, MNN hot-path trace evidence. |
| AWS connector | `scripts/aws` and Android bootstrap | Uploads, schedules, downloads, and verifies Device Farm artifacts. |

## Model Package And Loader

The final package is produced by `customlib/packer/pack_qwen35_xq4.py`.

The packer writes:

- W4A16 matrices for `q_proj`, `k_proj`, `v_proj`, `o_proj`
- W4A16 matrices for `gate_proj`, `up_proj`, `down_proj`
- W4A16 linear-attention matrices: `in_proj_qkv`, `in_proj_a`, `in_proj_b`, `in_proj_z`, `out_proj`
- W4A16 `lm_head.weight`
- BF16 embeddings in `embeddings_bf16.bin`
- F32 RMSNorm, Q/K norm, final norm, RoPE and linear-attention metadata
- F32 linear-attention tensors: `conv1d.weight`, `A_log`, `dt_bias`
- `xqwen35_manifest.json` with model dimensions, head counts, group size, RoPE theta, and partial rotary factor

The runtime loader in `CustomModel::load` validates the manifest, loads the layer files, loads `lm_head_weight.xq4`, and sizes the hidden, attention, FFN, recurrent state, and logits buffers.

## Generated W4A16 GEMV

The final generated W4 path is `customlib/kernels/generated/arm64_neon/xq_gemv_w4a16_neon.cpp`.

This file is the generated/tiled fused dequant + GEMV implementation used by the benchmarked custom path. It does not call `gemvLowBitReference`.

The kernel computes, per row and quantization group:

```text
code_dot = sum(code_i * activation_i)
x_sum    = sum(activation_i)
partial  = scale * (code_dot - zero * x_sum)
```

The arm64 NEON path processes 16 int4 codes at a time with byte loads, nibble unpacking, widening conversion, and vector FMA. The scalar tail handles uneven groups and the non-NEON host build. The final Qwen3.5 shapes exercised by Device Farm include:

- 4096 x 4096 attention and output projections
- 12288 x 4096 MLP gate/up projections
- 4096 x 12288 MLP down projection
- grouped key/value projection shapes used by the full-attention layers
- 248320 x 4096 `lm_head`

## Custom Prefill

`CustomModel::prefill` runs over every prompt token. It is not a last-token-only prefill.

For each prompt position it:

- reads the BF16 embedding row for that token
- runs every layer in order
- appends K/V into full-attention layer caches
- updates linear-attention recurrent state in linear-attention layers
- records `prefill_token_custom`
- records `prefill_kv_build_custom` when a full-attention layer appends K/V during prefill

The final Device Farm custom trace contains 512 `prefill_token_custom` calls for the 512-token prompt.

## Custom Full-Attention Decode

`CustomModel::runFullAttention` implements grouped-query decode attention.

The operation order is:

1. Apply input RMSNorm.
2. Run custom W4A16 `q_proj`, `k_proj`, and `v_proj`.
3. Apply Q/K norm where the layer provides Qwen3.5 q_norm/k_norm weights.
4. Apply RoPE to Q/K for the current absolute position.
5. Append K/V to the per-layer cache.
6. Map each query head to the correct KV head.
7. Compute `score = dot(q, k) / sqrt(head_dim)`.
8. Run max-subtracted softmax.
9. Reduce with V.
10. Apply attention output gate.
11. Run custom W4A16 `o_proj`.

Trace rows include:

- `linear_q_proj_w4a16`
- `linear_k_proj_w4a16`
- `linear_v_proj_w4a16`
- `rope_qk_custom`
- `kv_append_custom`
- `attention_score_custom`
- `attention_softmax_custom`
- `attention_v_reduce_custom`
- `attention_output_gate_custom`
- `linear_o_proj_w4a16`

## Custom Linear-Attention State

`CustomModel::runLinearAttention` replaces the earlier placeholder state logic.

The runtime maintains recurrent state per linear-attention layer. During prefill and decode it reads and updates that state using exported linear-attention tensors:

- `linear_attn_in_proj_a_weight.xq4`
- `linear_attn_in_proj_b_weight.xq4`
- `linear_attn_in_proj_qkv_weight.xq4`
- `linear_attn_in_proj_z_weight.xq4`
- `linear_attn_out_proj_weight.xq4`
- `linear_attn_conv1d_weight.f32`
- `linear_attn_A_log.f32`
- `linear_attn_dt_bias.f32`

The measured path records:

- `linear_attention_conv1d_custom`
- `linear_attention_qk_l2norm_custom`
- `linear_attention_state_update_custom`
- `linear_attention_gated_rmsnorm_custom`
- `linear_attn_out_proj_w4a16`

The implementation is the most faithful recurrent update available from the exported Qwen3.5 tensors in the custom package. It keeps state across all prompt and generated positions and does not use the old tanh/hash placeholder path.

## FFN, RMSNorm, And RoPE

The custom runtime implements RMSNorm, RoPE, and FFN gate math directly in `custom_model.cpp`.

FFN order:

```text
post_attention_rmsnorm
gate_proj W4A16
up_proj W4A16
silu(gate) * up
down_proj W4A16
residual add
```

Trace rows include:

- `rmsnorm_input`
- `rmsnorm_post_attention`
- `rmsnorm_final`
- `linear_gate_proj_w4a16`
- `linear_up_proj_w4a16`
- `silu_gate_mul_custom`
- `linear_down_proj_w4a16`

## Real lm_head And Greedy Sampling

The final custom path removes hash-based token generation.

`CustomModel::sampleGreedy`:

1. Applies final RMSNorm.
2. Runs `lm_head_custom` with the packed W4A16 `lm_head.weight`.
3. Computes greedy argmax over real logits.
4. Returns the selected token.

Trace rows include:

- `lm_head_custom`
- `sampling_greedy_custom`

The final benchmark settings use `temperature = 0`, `top_k = 1`, and `top_p = 1`, so greedy argmax is the required sampling behavior.

## Connectors

### MNN Connector

The stock baseline is implemented in `android/app/src/main/cpp/stock_benchmark_jni.cpp`. It creates `MNN::Transformer::Llm`, calls stock MNN generation, and records stock prefill TPS, decode TPS, TPOT, and instrumentation artifacts.

The custom APK also contains an MNN hot-path trace helper in `android/benchmark_app/src/main/cpp/benchmark_jni.cpp`. That helper runs after measured custom generation to collect MNN op type/name wall clock evidence. It is not on the measured custom generation path.

### Fallback Connector

`customlib/runtime/session.cpp` still supports `xq_options.use_mnn_fallback != 0` for debugging or compatibility. In that mode, `Session` creates an MNN LLM instance.

The final custom Device Farm run does not use that mode. The JSON evidence reports `use_mnn_fallback = 0` and `calls_mnn_llm_response_for_measured_generation = false`.

### JNI Connector

The JNI bridge exposes two instrumentation entry points:

- `NativeStockBenchmark.runBenchmark(...)`
- `NativeBenchmark.runBenchmark(...)`

Both accept prompt length, max new tokens, prompt token id, warmup iterations, measured iterations, and model directory. Both return `BENCH_RESULT_JSON` and write JSON artifacts under the Device Farm log directory.

### Benchmark Connector

The custom benchmark JSON is assembled in `android/benchmark_app/src/main/cpp/benchmark_jni.cpp`.

It records:

- selected kernels and op coverage
- `fallback_op_families = []`
- custom path booleans proving the measured path did not call MNN generation
- per-run prefill/decode timing
- measured mean TPS/TPOT
- `per_kernel_wall_clock`
- MNN hot-path trace evidence
- model package and benchmark settings

### Device Farm Connector

The Android instrumentation bootstrap downloads split model parts, reassembles the zip, verifies SHA-256, unzips the package, and deletes the zip to preserve device storage.

Final Device Farm evidence:

- Stock run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/baed9f8e-2a52-4b93-8584-60c305b73757`
- Custom run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7bc0f1d8-7640-4574-8309-da6bdb9fa642`
- Device: Samsung Galaxy S26 Ultra, SM-S948U1, Android 16
- Full model SHA-256 verified on-device: `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`

## Final Measured Coverage

`CustomModel::coverageSummary` reports:

```text
custom_decode_loop;hotpath_replaced=true;full_custom_decode=true;linear=q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj,linear_attn_qkv_a_b_z_out,lm_head;rmsnorm=custom;rope=custom;attention=custom_gqa_decode;linear_attention_state=custom_gated_delta;sampling=custom_greedy;prefill_kv_build=custom;fallback_ops=none
```

Final replaced op families:

| Family | Final path |
| --- | --- |
| q_proj | custom W4A16 GEMV |
| k_proj | custom W4A16 GEMV |
| v_proj | custom W4A16 GEMV |
| o_proj | custom W4A16 GEMV |
| gate_proj | custom W4A16 GEMV |
| up_proj | custom W4A16 GEMV |
| down_proj | custom W4A16 GEMV |
| rmsnorm | custom runtime math |
| rope | custom runtime math |
| attention | custom grouped-query decode attention |
| linear_attention_state | custom recurrent state update |
| lm_head | custom W4A16 logits |
| sampling | custom greedy argmax |
| prefill_kv_build | custom per-token cache build |

Fallback op families in the measured custom path: none.

## Test Coverage

Host tests are integrated through the CMake test flow:

```powershell
$env:PATH = "C:\msys64\ucrt64\bin;$env:PATH"
cmake -S . -B build-host -G Ninja -DXQ_BUILD_TESTS=ON
cmake --build build-host
ctest --test-dir build-host --output-on-failure
```

Final host result: 2/2 tests passed.

Required checks covered:

- stable softmax vs scalar reference
- grouped-query attention decode vs scalar reference
- KV cache append/read
- RoPE shape/position sanity
- RMSNorm sanity
- W4A16 GEMV against reference
- lm_head argmax against scalar reference
- greedy sampling
- prefill builds KV cache length correctly
- tiny end-to-end custom decode with toy dimensions

## Final Benchmark Verdict

The final v16 benchmark satisfies the requested same-device comparison and full custom path coverage.

It does not show a speedup:

- Stock decode TPS: 2.28587
- Custom decode TPS: 0.424895
- Custom / stock decode ratio: 0.1859x
- Stock is 5.38x faster on decode TPS

The correct claim is: the requested fallback families were implemented and measured in the custom path, but further optimization is needed before claiming performance leadership over stock MNN.

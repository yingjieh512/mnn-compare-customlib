# Kernel Walkthrough

The final v16 custom library is organized around generated W4A16 kernels plus custom runtime operators for attention, recurrent linear attention, lm_head, sampling, and prefill state build. The complete walkthrough is in `docs/kernel_library_code_walkthrough_final.md`.

## Final Kernel Set

- Generated W4A16 GEMV: `customlib/kernels/generated/arm64_neon/xq_gemv_w4a16_neon.cpp`
- RMSNorm: `customlib/runtime/custom_model.cpp`
- RoPE: `customlib/runtime/custom_model.cpp`
- Grouped-query full-attention decode: `customlib/runtime/custom_model.cpp`
- Linear-attention recurrent state update: `customlib/runtime/custom_model.cpp`
- FFN gate multiply: `customlib/runtime/custom_model.cpp`
- Real `lm_head` logits: `customlib/runtime/custom_model.cpp`
- Greedy sampling: `customlib/runtime/custom_model.cpp`
- Prefill K/V build: `customlib/runtime/custom_model.cpp`

The W4A16 generated kernel is a fused dequant + GEMV implementation. The W4 path does not call `gemvLowBitReference`.

## Packing Layout

Weights are row-major and bitpacked per output row:

- W4: two weights per byte.
- Each row is split into groupwise quantization groups.
- Each group stores `scale` and `zero`.
- Dequantization is `weight = (code - zero) * scale`.

The final comparison uses W4 group size 64.

## Replaced Families In The Final Measured Path

```text
q_proj
k_proj
v_proj
o_proj
gate_proj
up_proj
down_proj
rmsnorm
rope
attention
linear_attention_state
lm_head
sampling
prefill_kv_build
```

Final measured fallback families: none.

## Correctness Tests

`xq_kernel_correctness` and `xq_runtime_correctness` verify:

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

The final host CMake test run passed 2/2 tests.

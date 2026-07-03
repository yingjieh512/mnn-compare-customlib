# Kernel Walkthrough

The custom library is organized around generated low-bit decode kernels plus reference implementations used for correctness.

## Current Kernel Set

- W4A16 GEMV: `customlib/kernels/generated/arm64_neon/xq_gemv_w4a16_neon.cpp`
- W3A16 GEMV: `customlib/kernels/generated/arm64_neon/xq_gemv_w3a16_neon.cpp`
- W2A16 GEMV: `customlib/kernels/generated/arm64_neon/xq_gemv_w2a16_neon.cpp`
- RMSNorm reference: `customlib/kernels/reference/ref_rmsnorm.cpp`
- RoPE reference: `customlib/kernels/reference/ref_rope.cpp`
- GQA attention decode reference: `customlib/kernels/reference/ref_attention.cpp`
- Gated Delta decode reference: `customlib/kernels/reference/ref_delta.cpp`

The generated wrappers currently delegate to the verified low-bit reference path. The next optimization step is to replace the inner dequant-dot loop with shape-specialized arm64 NEON, dotprod, and i8mm variants after Device Farm profiling identifies the bottleneck.

## Packing Layout

Weights are row-major, bitpacked per output row:

- W4: two weights per byte.
- W3: eight weights per three bytes, with tail handling.
- W2: four weights per byte.

Each row is split into groupwise quantization groups. Each group stores `scale` and `zero`; dequantization is:

```text
weight = (code - zero) * scale
```

The headline comparison uses W4 group size 64. W2/W3 are experimental unless stock MNN can run the same bitwidth fairly.

## Correctness

`xq_kernel_correctness` verifies:

- Low-bit pack/dequant GEMV versus dense dequantized reference.
- RMSNorm numeric path.
- RoPE finite output.
- GQA attention decode softmax path.
- Gated Delta recurrent update.

The tests fail on mismatches and are intended to run on host and Android.

## Dispatcher

`customlib/kernels/generated/generated_dispatch.cpp` records selected kernels and CPU features. Final Device Farm runs must include this string in benchmark JSON.


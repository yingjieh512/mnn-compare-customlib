# Optimization Log

## 2026-07-03 Setup

- Hypothesis: create a reproducible baseline structure before optimizing hot kernels.
- Change: pinned MNN, verified Qwen3.5 HF revision, added C ABI, runtime skeleton, kernel references, generator stubs, Android benchmark modules, AWS automation, and benchmark parsers.
- Correctness status: host tests are expected to verify low-bit pack/dequant GEMV, RMSNorm, RoPE, attention, delta, and runtime C ABI.
- Benchmark before/after: no final Device Farm numbers because real Qwen3.5-9B model artifacts and stock/custom final runners were not executed.
- AWS status: exact Samsung Galaxy S26 Ultra is available and an exact-device pool was created.
- Next bottleneck: download/convert/pack the 19.33GB model, upload it through external data/S3, run stock and custom benchmarks, collect per-op decode profile, then replace W4 reference GEMV inner loop with shape-specialized arm64 NEON/dotprod/i8mm kernels.

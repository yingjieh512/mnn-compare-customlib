# Benchmark Methodology

The final headline comparison is the v16 AWS Device Farm run documented in `results/reports/final_devicefarm_report.md`.

## Fixed Inputs

- Model: `Qwen/Qwen3.5-9B`
- Revision: `c202236235762e1c871ad0ccb60c8ee5ba337b9a`
- Quantization: W4A16 groupwise, group size 64
- Prompt length: 512 tokens
- Decode length: 256 generated tokens
- Prompt token id: 16
- Batch size: 1
- Decode settings: greedy, temperature 0, top_k 1, top_p 1
- Backend: CPU
- Device: AWS Device Farm Samsung Galaxy S26 Ultra, SM-S948U1, Android 16
- Warmup / measured iterations: 1 / 3 for both stock and custom

The measured count was set to 3 for both engines because the complete custom path takes roughly 129 Device Farm device-minutes and must fit the 150-minute run limit. The same count is used for stock and custom.

## Metrics

```text
prefill_tokens_per_second = prompt_tokens / prefill_wall_time_seconds
decode_tokens_per_second = generated_decode_tokens / decode_wall_time_seconds
decode_tpot_ms = decode_wall_time_ms / generated_decode_tokens
```

Decode time excludes model load, APK startup, artifact download, and prefill. It includes all per-token generation compute.

## Final Result

| Metric | Stock MNN | Customlib |
| --- | ---: | ---: |
| Prefill TPS | 45.0960 | 0.486717 |
| Decode TPS | 2.28587 | 0.424895 |
| Decode TPOT | 437.470 ms | 2353.52 ms |

Custom / stock decode ratio: 0.1859x. No speedup is claimed.

## Device Evidence

The final report records:

- Device Farm project, device pool, run, job, and artifact identifiers.
- On-device model zip SHA-256 verification.
- Stock and custom `BENCH_RESULT_JSON`.
- Custom selected kernels and fallback family evidence.
- Custom per-kernel wall-clock table.
- MNN hot-path trace table.

## Fairness Rules

- Stock MNN and customlib must use the same device pool, model package, prompt length, decode length, generation settings, backend class, warmup count, and measured count.
- The custom report must not claim speedup when custom TPS is lower.
- The custom report must not claim full custom decode unless `fallback_op_families = []` and the measured custom path does not call MNN generation.

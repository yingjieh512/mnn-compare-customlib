# Benchmark Methodology

The headline comparison must contain exactly comparable stock MNN and customlib runs.

## Fixed Inputs

- Model: `Qwen/Qwen3.5-9B`
- Revision: `c202236235762e1c871ad0ccb60c8ee5ba337b9a`
- Prompt token count: same for both engines.
- Quantization: W4 groupwise, group size 64.
- Batch size: 1.
- Decode: greedy, temperature 0, top_k 1 or disabled, top_p 1.
- Same phone and same backend class for the headline row.

## Metrics

```text
prefill_tokens_per_second = prompt_tokens / prefill_wall_time_seconds
decode_tokens_per_second = generated_decode_tokens / decode_wall_time_seconds
```

Decode time excludes model load, tokenizer, app startup, artifact download, and prefill. It includes all actual per-token compute.

## Runs

- Prompt lengths: 128, 512, 2048 tokens.
- Optional: 8192 tokens.
- max_new_tokens: 256 minimum.
- Warmup: one short generation or discard first 16 decode tokens.
- Repetitions: at least 5 per engine/backend/config.
- Headline statistic: median. Also report min, max, p90.

## Device Evidence

Record:

- `getprop` manufacturer/model/device/hardware/board/fingerprint.
- `/proc/cpuinfo`.
- Vulkan/OpenCL availability where accessible.
- NNAPI/QNN probes where accessible.
- thermalservice and battery before/after.
- AWS Device Farm project/run/job/device/artifact identifiers.

## Fairness

Never compare custom W2 against stock MNN W4 as the main speedup. Never use a shorter context for customlib. Never omit the stock MNN baseline.


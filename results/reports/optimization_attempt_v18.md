# v18r2 Optimization Attempt And v19r2 Quality Rejection

## Outcome

Outcome B: no new official final result accepted.

The v18r2 runtime optimization improved measured custom performance, but the required v19r2 output-quality validation failed. Per the acceptance policy, v17 remains the official final delivery.

## What Was Tried

- Reused embedding file handles and embedding row buffers.
- Reserved full-attention KV cache capacity before prefill/decode.
- Reused attention/FFN scratch buffers.
- Reduced allocation and resize work in decode and prefill.
- Preserved full custom path guardrails: no `MNN::Llm::response` in measured custom generation and no fallback op families.
- Added Android quality-validation mode for stock and custom benchmarks.
- Added host comparison script: `scripts/quality/compare_quality_validation.py`.

## Tests

Host correctness tests passed before Device Farm:

```powershell
cmake -S . -B build-host-opt -G Ninja -DXQ_BUILD_TESTS=ON
cmake --build build-host-opt
ctest --test-dir build-host-opt --output-on-failure
```

Result: `2/2` tests passed.

Android build also passed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_android.ps1
```

## Performance Candidate

The performance candidate ran the full Qwen3.5-9B package on AWS Device Farm:

- Run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1b18e97c-38fe-4581-97c8-b7688b5fbc91`
- Custom decode TPS: `2.14021`
- Custom decode TPOT: `467.244 ms`
- v17 baseline decode TPS: `1.93417`
- v17 baseline decode TPOT: `517.018 ms`
- Delta: `+10.65%` decode TPS and `-49.774 ms` TPOT versus v17.

This passed the performance gate but was not sufficient for final acceptance after the quality guard was added.

## Quality Validation

Device Farm quality validation ran on the same Samsung Galaxy S26 Ultra pool and the same Qwen3.5-9B package.

| Run | ARN | Result |
| --- | --- | --- |
| Stock MNN quality v19r2 CPU | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/28a7b8ce-cb81-4e31-8498-c59164e9cdaa` | PASSED |
| Customlib quality v19r2 cpu_vulkan_hybrid request | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/e8582532-a655-4619-b348-9c07b5740f3d` | FAILED |

Quality verdict:

- Stock native quality gate: PASSED.
- Custom native quality gate: FAILED.
- Exact token match: `0 / 5`.
- Comparison-gate pass: `0 / 5`.
- Rejection reason: custom output was degenerate, mostly repeated token `220`; 4 of 5 prompts failed the repetition sanity gate.

Evidence:

- `results/reports/quality_validation_report.md`
- `results/reports/evidence/quality_validation_v19r2_stock.json`
- `results/reports/evidence/quality_validation_v19r2_custom.json`
- `results/reports/evidence/quality_validation_v19r2_comparison.json`
- `results/reports/evidence/stock_mnn_quality_v19r2_cpu_test_spec_redacted.yml`
- `results/reports/evidence/customlib_quality_v19r2_cpu_vulkan_hybrid_test_spec_redacted.yml`

## Final Decision

The optimized v18r2 custom result is rejected because output validation got worse and failed the deterministic token sanity guard. The official final result remains v17:

- Final report: `results/reports/final_devicefarm_report.md`
- Final JSON: `results/reports/final_devicefarm_report.json`
- Code walkthrough: `docs/kernel_library_code_walkthrough_final.md`

No custom speedup is claimed. No production-quality Qwen replacement is claimed.

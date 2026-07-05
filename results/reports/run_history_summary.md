# Device Farm Run History Summary

This file summarizes the major run families so the large `results/raw/**` expanded artifacts can be deleted locally without losing the audit trail. Final, machine-readable evidence is kept in `results/reports/evidence/`.

## Current Final: v17 Backend Sweep

Status: official final delivery. v18r2 remains a rejected experimental optimization after the v19r2 output-quality guard.

- Stock MNN CPU baseline run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7e44236c-db1a-4900-9fd8-7d8d7d654e28`
- Best accepted custom run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1de54984-c9d9-41d1-81c1-7eed941585ed`
- Device: Samsung Galaxy S26 Ultra, SM-S948U1, Android 16.
- Model: Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
- Model package SHA-256: `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`.
- Settings: 512 prompt tokens, 256 max_new_tokens, greedy sampling, 1 warmup + 3 measured.
- Stock CPU: prefill 45.6380 TPS, decode 2.27746 TPS, TPOT 439.086 ms.
- Best accepted custom: requested `cpu_vulkan_hybrid`, actual backend CPU; prefill 2.21477 TPS, decode 1.93417 TPS, TPOT 517.018 ms.
- Best custom / stock CPU decode ratio: 0.8493x.
- Verdict: requirement 1 YES, requirement 2 YES, Vulkan attempted YES, custom Vulkan kernels used NO, speedup NO.
- Evidence:
  - `results/reports/final_devicefarm_report.md`
  - `results/reports/final_devicefarm_report.json`
  - `results/reports/evidence/v17_backend_sweep_summary.json`
  - `results/reports/evidence/stock_mnn_cpu_benchmark_v17.json`
  - `results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v17.json`

## Rejected v18r2 Performance Candidate And v19r2 Quality Guard

Status: rejected; not official final.

- v18r2 performance run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1b18e97c-38fe-4581-97c8-b7688b5fbc91`.
- v18r2 performance candidate: decode 2.14021 TPS, TPOT 467.244 ms; this was faster than v17 custom but still slower than stock CPU.
- Stock quality run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/28a7b8ce-cb81-4e31-8498-c59164e9cdaa`, PASSED.
- Custom quality run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/e8582532-a655-4619-b348-9c07b5740f3d`, FAILED.
- Rejection reason: custom generated mostly repeated token `220`; exact token match 0/5; comparison-gate pass 0/5.
- Evidence:
  - `results/reports/optimization_attempt_v18.md`
  - `results/reports/quality_validation_report.md`
  - `results/reports/evidence/quality_validation_v19r2_comparison.json`

## v20 Accuracy Debug Attempt

Status: blocked; not official final.

- Purpose: continue from the v19/v20 repeated-token quality failure and patch concrete graph/runtime mismatches before re-running Device Farm validation.
- Source fixes applied: linear-attention gate semantics, linear-attention L2 epsilon placement, Qwen3.5 active-slice RoPE layout, and per-head q/gate deinterleave for full-attention q projection.
- Host result: `ctest --test-dir build-host-quality --output-on-failure` passed `2/2`.
- Android result: `scripts/build_android.ps1` completed with Gradle `BUILD SUCCESSFUL`.
- Device Farm result: patched custom quality runs did not produce a completed `BENCH_QUALITY_JSON`; repeated runs reached Setup/Teardown but the Tests Suite was STOPPED before instrumentation evidence was emitted.
- v17 remains the official final benchmark and no new quality or speedup claim is made.
- Evidence:
  - `results/reports/quality_debug_blocker.md`
  - `results/reports/evidence/quality_validation_v20_devicefarm_blocker_runs.json`

## v17 Optimization And Backend Sweep

Status: official final backend sweep. v18r2 is kept only as a rejected experimental attempt after the quality guard.

- Stock MNN CPU run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7e44236c-db1a-4900-9fd8-7d8d7d654e28`
- Stock MNN Vulkan-request run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/067c195b-1e14-4bca-998d-c7d38a65c5c7`
- Customlib CPU run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/8d765268-aacd-4f52-b845-f5370b4d522f`
- Customlib CPU/Vulkan-hybrid-request run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1de54984-c9d9-41d1-81c1-7eed941585ed`
- Device: Samsung Galaxy S26 Ultra, SM-S948U1, Android 16.
- Model: Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
- Model package SHA-256: `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`.
- Settings: 512 prompt tokens, 256 max_new_tokens, greedy sampling, 1 warmup + 3 measured.
- Stock CPU: prefill 45.6380 TPS, decode 2.27746 TPS, TPOT 439.086 ms.
- Stock Vulkan-request: initialized Vulkan, then process crashed before `BENCH_RESULT_JSON`; no TPS/TPOT.
- Custom CPU: prefill 2.13908 TPS, decode 1.85575 TPS, TPOT 538.865 ms.
- Custom hybrid-request: requested `cpu_vulkan_hybrid`, actual backend CPU; prefill 2.21477 TPS, decode 1.93417 TPS, TPOT 517.018 ms.
- Best custom / stock CPU decode ratio: 0.8493x.
- Verdict: requirement 1 YES, requirement 2 YES, Vulkan attempted YES, custom Vulkan kernels used NO, speedup NO.
- Evidence:
  - `results/reports/final_devicefarm_report.md`
  - `results/reports/final_devicefarm_report.json`
  - `results/reports/evidence/v17_backend_sweep_summary.json`
  - `results/reports/evidence/stock_mnn_cpu_benchmark_v17.json`
  - `results/reports/evidence/stock_mnn_vulkan_benchmark_failure_v17.json`
  - `results/reports/evidence/customlib_cpu_benchmark_v17.json`
  - `results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v17.json`

## v16 Full Custom Decode Baseline

Status: superseded by v17, but kept for performance-improvement audit trail.

- Stock MNN CPU run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/baed9f8e-2a52-4b93-8584-60c305b73757`
- Customlib CPU run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7bc0f1d8-7640-4574-8309-da6bdb9fa642`
- Stock CPU: prefill 45.0960 TPS, decode 2.28587 TPS, TPOT 437.470 ms.
- Custom CPU: prefill 0.486717 TPS, decode 0.424895 TPS, TPOT 2353.52 ms.
- Custom / stock decode ratio: 0.1859x.
- v17 improved custom CPU decode from 0.424895 TPS to 1.85575 TPS, while still remaining slower than stock MNN.

## v15 Full Custom Timeout Attempt

Status: historical attempt, not final.

- Purpose: first full-custom path Device Farm attempt with 1 warmup + 5 measured custom iterations.
- Result: custom run exceeded the 150-minute Device Farm limit after warmup plus only part of the measured set.
- Useful evidence: the run showed the full custom path was real but too slow for 1 + 5 iterations.
- Resolution: v16 and v17 used 1 warmup + 3 measured iterations for full-model comparisons.

## v14 Hotpath Bring-Up

Status: historical, partial custom hotpath run.

- Stock MNN run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/a2f55f2f-b13f-4abf-8362-79810afd58ef`
- Custom hotpath run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/c3353a1b-56f6-4a2e-87ab-f4bd20b3416a`
- Same prompt/settings/device as later runs, but custom path still had explicit fallbacks for attention, linear_attention_state, lm_head, sampling, and prefill_kv_build.
- Stock median decode TPS: 2.266760.
- Custom hotpath median decode TPS: 0.561446.
- Custom / stock decode ratio: 0.2477x.
- Verdict: useful hotpath bring-up, not a full faithful final benchmark.

## v13 Full Embeddings

Status: historical, superseded.

- Purpose: earlier full-embeddings packaging and Device Farm artifact path validation.
- The retained markdown file is not used as final evidence because later v14/v16/v17 reports supersede it.
- Do not cite v13 as the final benchmark.

## Earlier Real-Download / Sparse / Smoke Attempts

Status: historical failures or automation checks, not final.

- Several early runs validated Device Farm project/device pool creation, model download, split-upload handling, and Android bootstrap behavior.
- Smoke runs and partial/failing real-download runs must not be reported as final performance results.
- Expanded raw artifacts can be deleted locally after small evidence files are retained.

## Local Cleanup Result

Cleanup policy:

- Delete generated build dirs, Android build outputs, `.venv-export`, expanded raw artifacts, old hotpath packages, duplicate unpacked model packages, private Device Farm upload specs, and presentation render scratch folders.
- Keep source code, scripts, docs, final reports, final small evidence, `models/Qwen3.5-9B`, and `out/qwen35_xq_fullcustom_v15.zip` unless the model zip is explicitly removed.

Post-cleanup local model assets:

- `models/Qwen3.5-9B`: base HF model, about 36GB.
- `out/qwen35_xq_fullcustom_v15.zip`: final Device Farm model package, 11,266,405,198 bytes, SHA-256 `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`.

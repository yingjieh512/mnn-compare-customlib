# v20 Accuracy Debug Attempt And Device Farm Blocker

## Outcome

Outcome C: quality is still blocked, and no new official final result is accepted.

The v20 pass found and patched three concrete custom-runtime correctness issues, but the patched custom APK did not complete Device Farm quality validation. Because there is no `BENCH_QUALITY_JSON` from the patched APK, this result is not accepted as a new final delivery and does not replace v17.

The official final remains:

- Final report: `results/reports/final_devicefarm_report.md`
- Final JSON: `results/reports/final_devicefarm_report.json`
- Code walkthrough: `docs/kernel_library_code_walkthrough_final.md`

## Root Causes Investigated

The starting custom quality failure was repeated token `220` on the fixed validation prompts. v20 investigated the MNN graph and custom runtime rather than renaming the failure.

Concrete fixes applied:

- Linear-attention gate semantics: the MNN graph feeds `FusedLinearAttention` with `beta = sigmoid(in_proj_b)` and `gate = -1.000001 * softplus(in_proj_a + 1e-6)`. The custom runtime previously used `A_log` and `dt_bias` in the gate, which did not match the exported graph.
- Linear-attention Q/K L2 normalization: MNN uses `1 / sqrt(sum + 1e-6)`. The custom runtime now matches this epsilon placement.
- Qwen3.5 partial RoPE layout: Qwen3.5 exports `phi_rotary_pos`, rotating only the first `rotary_dim` values and splitting inside that active slice. The custom runtime now rotates `0..rotary_dim/2-1` with `rotary_dim/2..rotary_dim-1` and passes the remaining head dimensions through.
- Full-attention q/gate split: the MNN graph reshapes q projection as `[num_heads, 512]` and splits each head into `256 query + 256 gate`. The custom runtime previously treated the first contiguous 4096 values as query and the second 4096 as gate. It now deinterleaves per head.

## Tests Run

Host tests were rebuilt and passed after the patches:

```powershell
$env:PATH='C:\Users\Yingjie Huang\qwen-phone-npu-trial\third_party\toolchains\w64devkit\bin;' + $env:PATH
& 'C:\Users\Yingjie Huang\AppData\Local\Android\Sdk\cmake\3.22.1\bin\cmake.exe' --build build-host-quality
& 'C:\Users\Yingjie Huang\AppData\Local\Android\Sdk\cmake\3.22.1\bin\ctest.exe' --test-dir build-host-quality --output-on-failure
```

Result: `2/2` tests passed.

Android rebuild also passed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_android.ps1
```

Result: Gradle `BUILD SUCCESSFUL`.

## Device Farm Evidence

The same model package and target device were used:

- Model package SHA-256: `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`
- Device: Samsung Galaxy S26 Ultra, Android 16
- Original exact pool: `arn:aws:devicefarm:us-west-2:884244642857:devicepool:64d2cc31-abd6-49f8-97da-162f82410bc0/14d31c96-b8fc-4930-99c7-1a8948124213`
- Retry exact pool: `arn:aws:devicefarm:us-west-2:884244642857:devicepool:64d2cc31-abd6-49f8-97da-162f82410bc0/e74ce3c0-d57f-475a-915e-858da2d54bea`
- Device ARN in both pools: `arn:aws:devicefarm:us-west-2::device:536B9FDAEAA14A11B504A3ECC86DA717`

Run status evidence is retained in:

- `results/reports/evidence/quality_validation_v20_devicefarm_blocker_runs.json`

Key runs:

| Run | ARN | Result | Note |
| --- | --- | --- | --- |
| v20r2 stock quality | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/d9f94d76-9bac-4e97-aeea-21c9a12500bc` | PASSED | Stock reference quality JSON exists. |
| v20r2 current custom quality | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/883dc900-f327-4497-ab59-ce2e82eda7af` | FAILED | Repeated token `220`; real quality failure. |
| v20r3 gate-fix custom | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7084ce6e-de9f-447e-8a5b-2c7e80e3865f` | STOPPED | Obsolete after discovering RoPE and q/gate bugs. |
| v20r6 patched custom | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/acce7705-c7b6-4930-bb52-b661b0719264` | STOPPED | Tests Suite did not complete; no `BENCH_QUALITY_JSON`. |
| v20r6b patched custom retry | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/d09ab26b-4f54-4e66-b716-42f1fee60a1f` | STOPPED | Same APK/spec; Tests Suite did not complete. |
| v20r7 patched custom retry | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/8ef6edff-c7bf-461c-b599-42d0745137c8` | STOPPED | Same APK/spec; Tests Suite did not complete. |
| v20r8 patched custom retry, new exact pool | `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/f9f9cfe7-a43b-4c40-abe9-0b18ffa2ee92` | STOPPED | New pool, same device ARN; Tests Suite did not emit quality JSON. |

## Acceptance Decision

The v20 code changes are plausible correctness fixes and are backed by host tests plus MNN graph inspection, but the required Device Farm quality gate did not produce a completed custom validation JSON for the patched APK.

Therefore:

- New official final accepted: NO
- Production-quality Qwen replacement claimed: NO
- Token-level equivalence claimed: NO
- Speedup claimed: NO
- v17 remains official systems/kernel benchmark final: YES


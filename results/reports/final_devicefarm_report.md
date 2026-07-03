# Final Device Farm Report

Status: `BLOCKED_MODEL_ARTIFACTS_AND_FINAL_RUN_NOT_EXECUTED`

Exact Device Farm device was found:

- Device ARN: `arn:aws:devicefarm:us-west-2::device:536B9FDAEAA14A11B504A3ECC86DA717`
- Device name: `Samsung Galaxy S26 Ultra`
- Model ID: `SM-S948U1`
- OS: `16`
- Availability: `HIGHLY_AVAILABLE`

AWS resources prepared:

- Project ARN: `arn:aws:devicefarm:us-west-2:884244642857:project:64d2cc31-abd6-49f8-97da-162f82410bc0`
- Device pool ARN: `arn:aws:devicefarm:us-west-2:884244642857:devicepool:64d2cc31-abd6-49f8-97da-162f82410bc0/14d31c96-b8fc-4930-99c7-1a8948124213`

No final tokens/sec are claimed because the real Qwen3.5-9B model artifacts were not downloaded, converted, packed, uploaded, and executed through the stock/custom runners.

| Engine | Prefill tok/s | Decode tok/s | Median | Min | Max | P90 |
|---|---:|---:|---:|---:|---:|---:|
| stock MNN | 0 | 0 | 0 | 0 | 0 | 0 |
| customlib | 0 | 0 | 0 | 0 | 0 | 0 |

Speedup ratio: `0.0000x`

`>=20 decode tok/s`: `FAIL_NOT_RUN`

Raw setup artifacts:

- `results/raw/devicefarm_devices.json`
- `results/raw/aws_resources.json`
- `results/devicefarm_blocker.md`


# Historical Device Farm Blocker, Resolved By v16

This file is retained only as an audit trail for the earlier July 2026 state where the real Qwen3.5-9B model package had not yet been packed and executed on AWS Device Farm.

The blocker described here is no longer the final project state. It was resolved by the v16 final Device Farm runs documented in:

- `results/reports/final_devicefarm_report.md`
- `results/reports/final_devicefarm_report.json`
- `results/reports/evidence/stock_mnn_benchmark_v16_final.json`
- `results/reports/evidence/customlib_benchmark_v16_final.json`

Resolved evidence:

- Stock MNN run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/baed9f8e-2a52-4b93-8584-60c305b73757`
- Customlib run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7bc0f1d8-7640-4574-8309-da6bdb9fa642`
- Device: Samsung Galaxy S26 Ultra, model ID SM-S948U1, Android 16
- Model package SHA-256 verified on-device: `9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34`

Final status:

- Faithful benchmark: YES
- Requirement 1 met: YES
- Requirement 2 met: YES
- Custom speedup claim allowed: NO
- Reason: custom decode TPS was 0.1859x stock MNN decode TPS on the final same-device run.

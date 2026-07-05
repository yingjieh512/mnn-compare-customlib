# Qwen3.5-9B Device Farm Final Summary

- Version: v18r2 optimization final.
- Requirement 1 met: YES.
- Requirement 2 met: YES.
- Stock MNN CPU: prefill 45.6380 TPS, decode 2.27746 TPS, TPOT 439.086 ms.
- Customlib v18r2: prefill 2.44242 TPS, decode 2.14021 TPS, TPOT 467.244 ms.
- Custom/stock decode ratio: 0.9397x.
- v18r2 vs v17 best custom decode: +10.65% TPS, -49.774 ms TPOT.
- Speedup claimed: NO. Custom remains slower than stock MNN CPU.
- Final report: `results/reports/final_devicefarm_report.md`.
- Code walkthrough: `docs/kernel_library_code_walkthrough_final.md`.
- Custom v18r2 run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1b18e97c-38fe-4581-97c8-b7688b5fbc91`.

# Qwen3.5-9B Device Farm Final Summary v16

- Stock run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/baed9f8e-2a52-4b93-8584-60c305b73757`; PASSED.
- Custom run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7bc0f1d8-7640-4574-8309-da6bdb9fa642`; PASSED.
- Same settings: 512 prompt tokens, 256 max_new_tokens, greedy sampling, W4A16 groupwise, 1 warmup + 3 measured.
- Stock MNN: prefill 45.0960 TPS, decode 2.28587 TPS, TPOT 437.470 ms.
- Customlib: prefill 0.486717 TPS, decode 0.424895 TPS, TPOT 2353.52 ms.
- Custom/stock decode ratio: 0.1859x.
- Speedup claimed: NO. Stock is 5.38x faster by decode TPS.
- Custom measured path: `use_mnn_fallback=0`, `calls_mnn_llm_response_for_measured_generation=false`, `full_custom_decode=true`, `fallback_op_families=[]`.

See `results/reports/final_devicefarm_report.md`, `docs/kernel_library_code_walkthrough_final.md`, and `results/reports/qwen35_9b_full_custom_v16_presentation.pptx`.

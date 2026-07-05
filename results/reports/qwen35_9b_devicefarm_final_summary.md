# Qwen3.5-9B Device Farm Final Summary v17

- Stock CPU run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/7e44236c-db1a-4900-9fd8-7d8d7d654e28`; PASSED.
- Stock Vulkan-request run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/067c195b-1e14-4bca-998d-c7d38a65c5c7`; Vulkan initialized, then benchmark process crashed before JSON.
- Custom CPU run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/8d765268-aacd-4f52-b845-f5370b4d522f`; PASSED.
- Custom CPU/Vulkan-hybrid-request run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1de54984-c9d9-41d1-81c1-7eed941585ed`; PASSED, actual custom backend CPU.
- Same settings: 512 prompt tokens, 256 max_new_tokens, greedy sampling, W4A16 groupwise model package, 1 warmup + 3 measured.
- Stock CPU: prefill 45.6380 TPS, decode 2.27746 TPS, TPOT 439.086 ms.
- Custom CPU: prefill 2.13908 TPS, decode 1.85575 TPS, TPOT 538.865 ms.
- Best custom measured variant: custom `cpu_vulkan_hybrid` request, actual CPU; prefill 2.21477 TPS, decode 1.93417 TPS, TPOT 517.018 ms.
- Best custom / stock CPU decode ratio: 0.8493x.
- Speedup claimed: NO.
- Custom measured path: `use_mnn_fallback=0`, `calls_mnn_llm_response_for_measured_generation=false`, `full_custom_decode=true`, `fallback_op_families=[]`.
- Custom Vulkan kernel execution claimed: NO.

See `results/reports/final_devicefarm_report.md`, `results/reports/final_devicefarm_report.json`, `results/reports/evidence/v17_backend_sweep_summary.json`, `docs/kernel_library_code_walkthrough_final.md`, and `results/reports/qwen35_9b_v17_backend_sweep_presentation.pptx`.

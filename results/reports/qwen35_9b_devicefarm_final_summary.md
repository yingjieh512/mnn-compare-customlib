# Qwen3.5-9B Device Farm Final Summary

Status: `complete`

Device: Samsung Galaxy S26 Ultra (`SM-S948U1`), Android 16

| Engine | Backend | Prefill median tok/s | Decode median tok/s | Measured |
|---|---|---:|---:|---:|
| MNN stock | cpu | 45.6044 | 2.2995 | 5 |
| customlib | mnn_fallback_cpu | 45.7430 | 2.2552 | 5 |

Custom / stock decode ratio: `0.9808x`

Notes:
- customlib run used backend `mnn_fallback_cpu` with selected kernels: `customlib_api+mnn_llm_fallback; generated_arm64_kernels_present; hotpath_not_replaced`.
- stock Device Farm run was marked failed only because v8 spec treated `INSTRUMENTATION_CODE: -1` as failure; AndroidJUnitRunner output was `OK (1 test)` and logcat contains `status:"ok"` benchmark JSON.
- Model zip SHA256: `fee6c0a893836afa0bae83762c8b3800d71723a7e02c006c49605a8fa2866d1b`.

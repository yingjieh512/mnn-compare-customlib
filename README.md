# Qwen3.5-9B Custom MNN-Based Mobile Inference Library

This repository builds a custom MNN-based mobile LLM inference library for `Qwen/Qwen3.5-9B`, with generated low-bit kernels, model packing scripts, Android benchmark APKs, and AWS Device Farm automation.

Current pinned inputs:

- MNN: `0bff03cbef43c783f44e41484b9f8a0b28bd758d`
- Hugging Face model: `Qwen/Qwen3.5-9B`
- HF revision: `c202236235762e1c871ad0ccb60c8ee5ba337b9a`
- Headline quantization target: W4A16 groupwise, group size 64

## Status

The project skeleton, C ABI, reference/generated kernel path, Android benchmark modules, model packer, result parser, and AWS Device Farm scripts are present. Android APKs build successfully and AWS Device Farm has an exact Samsung Galaxy S26 Ultra available in `us-west-2`.

Final AWS Device Farm tokens/sec are not claimed in this checkout because the real Qwen3.5-9B model artifacts were not downloaded/converted/packed/uploaded and the stock MNN runner is still a smoke harness. See `results/devicefarm_blocker.md`.

Exact Device Farm device found:

- ARN: `arn:aws:devicefarm:us-west-2::device:536B9FDAEAA14A11B504A3ECC86DA717`
- Name: `Samsung Galaxy S26 Ultra`
- Model ID: `SM-S948U1`
- OS: `16`
- Availability: `HIGHLY_AVAILABLE`

## Build Host Correctness Tests

On this Windows workspace, Android SDK CMake is available even when `cmake` is not on `PATH`:

```powershell
$cmake="$env:LOCALAPPDATA\Android\Sdk\cmake\3.22.1\bin\cmake.exe"
& $cmake -S . -B build\host -G Ninja -DXQ_BUILD_TESTS=ON
& $cmake --build build\host
& $cmake --build build\host --target test
```

## Build Android APKs

```powershell
.\scripts\build_android.ps1
```

Expected outputs:

- `android/app/build/outputs/apk/release/app-release.apk`
- `android/app/build/outputs/apk/androidTest/release/app-release-androidTest.apk`
- `android/benchmark_app/build/outputs/apk/release/benchmark_app-release.apk`
- `android/benchmark_app/build/outputs/apk/androidTest/release/benchmark_app-release-androidTest.apk`

## Model Download, Conversion, and Packing

```bash
scripts/download_model.sh models/Qwen3.5-9B
scripts/convert_model.sh models/Qwen3.5-9B out/qwen35_mnn_w4
scripts/pack_model.sh models/Qwen3.5-9B out/qwen35_custom_w4 4 64
```

The packer reads `config.json` and records actual Qwen3.5 dimensions in `xqwen35_manifest.json`.

## AWS Device Farm Flow

```bash
python scripts/aws/check_credentials.py --region us-west-2
python scripts/aws/list_devicefarm_devices.py --region us-west-2
python scripts/aws/create_or_get_project.py --region us-west-2
python scripts/aws/create_exact_device_pool.py --project-arn PROJECT_ARN --region us-west-2
python scripts/aws/upload_artifact.py --project-arn PROJECT_ARN --path APP.apk --type ANDROID_APP
python scripts/aws/upload_artifact.py --project-arn PROJECT_ARN --path TEST.apk --type INSTRUMENTATION_TEST_PACKAGE
python scripts/aws/schedule_benchmark_run.py --project-arn PROJECT_ARN --app-arn APP_UPLOAD_ARN --test-package-arn TEST_UPLOAD_ARN --device-pool-arn DEVICE_POOL_ARN
python scripts/aws/wait_for_run.py --run-arn RUN_ARN
python scripts/aws/download_artifacts.py --run-arn RUN_ARN
python scripts/aws/make_report.py --raw-dir results/raw/RUN_DIR
```

Final validation must use an exact AWS Device Farm Samsung Galaxy S26 Ultra. Another phone may be used only for development smoke tests and must not be reported as the final result.

## Public C ABI

The exported API is in `customlib/include/xqwen35.h`:

- `xq_create`
- `xq_destroy`
- `xq_prefill`
- `xq_decode_one`
- `xq_generate`
- `xq_reset`
- `xq_get_last_metrics`
- `xq_get_backend_info`

The public API does not expose raw MNN APIs.

## Honesty Rules

This repository must not claim:

- Device Farm validation without run artifacts.
- NPU acceleration without backend/profiler evidence.
- A custom speedup unless stock MNN and customlib use the same model, revision, tokenizer, prompt, quantization, backend class, generation settings, and phone.

# AWS Device Farm Final Benchmark Blocker

- timestamp_utc: `2026-07-03T21:15:30Z`
- region: `us-west-2`
- exact_manufacturer_filter: `Samsung`
- exact_model_filter: `Galaxy S26 Ultra`
- reason: `Exact device is available, but final Qwen3.5-9B stock-vs-custom benchmark was not run because the real model artifacts and stock MNN runner are not yet packaged for Device Farm. Smoke APKs were built and uploaded only as automation artifacts; no smoke numbers are reported as final.`

## Exact Device Evidence

```json
{
  "arn": "arn:aws:devicefarm:us-west-2::device:536B9FDAEAA14A11B504A3ECC86DA717",
  "name": "Samsung Galaxy S26 Ultra",
  "manufacturer": "Samsung",
  "model": "Samsung Galaxy S26 Ultra",
  "modelId": "SM-S948U1",
  "platform": "ANDROID",
  "os": "16",
  "availability": "HIGHLY_AVAILABLE",
  "fleetType": "PUBLIC",
  "remoteAccessEnabled": true
}
```

## AWS Resources Created

```json
{
  "project_arn": "arn:aws:devicefarm:us-west-2:884244642857:project:64d2cc31-abd6-49f8-97da-162f82410bc0",
  "device_pool_arn": "arn:aws:devicefarm:us-west-2:884244642857:devicepool:64d2cc31-abd6-49f8-97da-162f82410bc0/14d31c96-b8fc-4930-99c7-1a8948124213",
  "customlib_app_upload_arn": "arn:aws:devicefarm:us-west-2:884244642857:upload:64d2cc31-abd6-49f8-97da-162f82410bc0/96d9e1df-4734-447b-9bfb-d48bce4d55ea",
  "customlib_test_upload_arn": "arn:aws:devicefarm:us-west-2:884244642857:upload:64d2cc31-abd6-49f8-97da-162f82410bc0/969bb67b-6f65-46df-ae8a-c6037f5fe6d0",
  "stock_app_upload_arn": "arn:aws:devicefarm:us-west-2:884244642857:upload:64d2cc31-abd6-49f8-97da-162f82410bc0/37325f3d-8371-4e28-a463-e52f0d6b9ae5",
  "stock_test_upload_arn": "arn:aws:devicefarm:us-west-2:884244642857:upload:64d2cc31-abd6-49f8-97da-162f82410bc0/fdf968a5-c782-4019-b1f8-5d8deb1fbb51"
}
```

## Model Artifact Evidence

```json
{
  "hf_repo": "Qwen/Qwen3.5-9B",
  "hf_revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
  "known_total_size_bytes": 19329393661,
  "weight_shards": [
    "model.safetensors-00001-of-00004.safetensors",
    "model.safetensors-00002-of-00004.safetensors",
    "model.safetensors-00003-of-00004.safetensors",
    "model.safetensors-00004-of-00004.safetensors"
  ],
  "blocker": "Weights were not downloaded, converted to MNN, packed to xpack, uploaded through S3/external data, or executed on Device Farm in this run."
}
```

## Next Action

Run the real model pipeline:

```bash
scripts/download_model.sh models/Qwen3.5-9B
scripts/convert_model.sh models/Qwen3.5-9B out/qwen35_mnn_w4
scripts/pack_model.sh models/Qwen3.5-9B out/qwen35_custom_w4 4 64
python scripts/aws/upload_artifact.py --project-arn arn:aws:devicefarm:us-west-2:884244642857:project:64d2cc31-abd6-49f8-97da-162f82410bc0 --path MODEL_PACKAGE --type EXTERNAL_DATA
```

Then schedule the stock and custom instrumentation runs on the exact device pool and generate `results/reports/final_devicefarm_report.md`.


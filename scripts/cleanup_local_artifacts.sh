#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXECUTE=0
REMOVE_MODEL_ASSETS=0
REMOVE_FINAL_MODEL_ZIP=0

for arg in "$@"; do
  case "$arg" in
    --execute) EXECUTE=1 ;;
    --remove-model-assets) REMOVE_MODEL_ASSETS=1 ;;
    --remove-final-model-zip) REMOVE_FINAL_MODEL_ZIP=1 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

targets=(
  "build"
  "build-host"
  "build-android-check"
  "build-host-opt"
  ".gradle"
  ".venv-export"
  "android/app/build"
  "android/app/.cxx"
  "android/benchmark_app/build"
  "android/benchmark_app/.cxx"
  "results/raw"
  "results/reports/qwen35_9b_full_custom_v16_presentation"
  "results/reports/qwen35_9b_devicefarm_v14_hotpath_presentation"
  "results/reports/qwen35_9b_kernel_library_walkthrough_devicefarm_v13"
  "results/reports/qwen35_9b_full_custom_v16_presentation.pptx.inspect.ndjson"
  "results/reports/qwen35_9b_devicefarm_v14_hotpath_presentation.pptx.inspect.ndjson"
  "results/reports/qwen35_9b_kernel_library_walkthrough_devicefarm_v13.pptx.inspect.ndjson"
)

if [[ "$REMOVE_MODEL_ASSETS" == "1" ]]; then
  targets+=("models" "out")
else
  targets+=(
    "out/devicefarm_private"
    "out/devicefarm_specs"
    "out/devicefarm_specs_private"
    "out/private_devicefarm_specs"
    "out/qwen35_custom_w4"
    "out/qwen35_mnn_skip"
    "out/qwen35_xq_fullcustom_v15"
    "out/qwen35_xq_fullcustom_v15_parts"
    "out/qwen35_xq_fullcustom_v17_parts"
    "out/qwen35_xq_hotpath"
    "out/qwen35_xq_hotpath_parts_v14"
    "out/qwen35_xq_hotpath_test"
    "out/tmp_probe"
    "out/old_custom_split_fullcustom_v16_measured3.yml"
    "out/qwen35_mnn_skip.zip"
    "out/qwen35_mnn_skip_no_embeddings.zip"
    "out/qwen35_xq_hotpath.zip"
  )
  if [[ "$REMOVE_FINAL_MODEL_ZIP" == "1" ]]; then
    targets+=("out/qwen35_xq_fullcustom_v15.zip")
  fi
fi

echo "Workspace: $ROOT"
echo "Mode: $([[ "$EXECUTE" == "1" ]] && echo EXECUTE || echo DRY-RUN)"
for rel in "${targets[@]}"; do
  path="$ROOT/$rel"
  [[ -e "$path" ]] || continue
  case "$(cd "$(dirname "$path")" && pwd -P)/$(basename "$path")" in
    "$ROOT"/*) ;;
    *) echo "Refusing to clean path outside workspace: $path" >&2; exit 3 ;;
  esac
  du -sh "$path" 2>/dev/null || true
done

if [[ "$EXECUTE" != "1" ]]; then
  echo "Dry-run only. Re-run with --execute to delete these paths."
  exit 0
fi

for rel in "${targets[@]}"; do
  path="$ROOT/$rel"
  [[ -e "$path" ]] || continue
  rm -rf "$path"
  echo "Deleted $rel"
done

echo "Cleanup complete."

#!/usr/bin/env bash
set -euo pipefail

REVISION="c202236235762e1c871ad0ccb60c8ee5ba337b9a"
OUT="${1:-models/Qwen3.5-9B}"
mkdir -p "$OUT"

if command -v huggingface-cli >/dev/null 2>&1; then
  huggingface-cli download Qwen/Qwen3.5-9B --revision "$REVISION" --local-dir "$OUT" --local-dir-use-symlinks False
elif command -v git-lfs >/dev/null 2>&1; then
  git lfs install
  git clone https://huggingface.co/Qwen/Qwen3.5-9B "$OUT"
  git -C "$OUT" checkout "$REVISION"
  git -C "$OUT" lfs pull
else
  echo "Install huggingface-cli or git-lfs to download Qwen/Qwen3.5-9B." >&2
  exit 2
fi


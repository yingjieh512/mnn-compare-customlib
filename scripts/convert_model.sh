#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR="${1:?usage: scripts/convert_model.sh MODEL_DIR OUT_DIR}"
OUT_DIR="${2:?usage: scripts/convert_model.sh MODEL_DIR OUT_DIR}"
python customlib/packer/convert_qwen35.py --model-dir "$MODEL_DIR" --out-dir "$OUT_DIR" --bits 4 --group-size 64


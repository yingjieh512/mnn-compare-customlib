#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR="${1:?usage: scripts/pack_model.sh MODEL_DIR OUT_DIR [bits] [group_size]}"
OUT_DIR="${2:?usage: scripts/pack_model.sh MODEL_DIR OUT_DIR [bits] [group_size]}"
BITS="${3:-4}"
GROUP="${4:-64}"
python customlib/packer/convert_qwen35.py --model-dir "$MODEL_DIR" --out-dir "$OUT_DIR" --bits "$BITS" --group-size "$GROUP" --skip-mnn-export
python customlib/packer/validate_pack.py "$OUT_DIR/xqwen35_manifest.json"


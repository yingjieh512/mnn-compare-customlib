#!/usr/bin/env python3
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
from typing import Dict, Any


PINNED_REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
HF_REPO = "Qwen/Qwen3.5-9B"


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_config(model_dir: pathlib.Path) -> Dict[str, Any]:
    cfg = model_dir / "config.json"
    if not cfg.exists():
        raise FileNotFoundError(f"missing {cfg}")
    data = json.loads(cfg.read_text(encoding="utf-8"))
    text_cfg = data.get("text_config", data)
    return {"raw": data, "text": text_cfg}


def model_facts(model_dir: pathlib.Path) -> Dict[str, Any]:
    cfg = read_config(model_dir)
    text = cfg["text"]
    return {
        "hf_repo": HF_REPO,
        "hf_revision": PINNED_REVISION,
        "model_type": text.get("model_type", cfg["raw"].get("model_type")),
        "hidden_size": text.get("hidden_size"),
        "head_dim": text.get("head_dim"),
        "num_attention_heads": text.get("num_attention_heads"),
        "num_key_value_heads": text.get("num_key_value_heads"),
        "num_hidden_layers": text.get("num_hidden_layers"),
        "vocab_size": text.get("vocab_size", cfg["raw"].get("vocab_size")),
        "intermediate_size": text.get("intermediate_size"),
        "layer_types": text.get("layer_types"),
        "linear_key_head_dim": text.get("linear_key_head_dim"),
        "linear_value_head_dim": text.get("linear_value_head_dim"),
        "linear_num_key_heads": text.get("linear_num_key_heads"),
        "linear_num_value_heads": text.get("linear_num_value_heads"),
        "max_position_embeddings": text.get("max_position_embeddings"),
        "rms_norm_eps": text.get("rms_norm_eps"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--mnn-dir", default="third_party/MNN")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--bits", type=int, default=4, choices=(2, 3, 4))
    parser.add_argument("--group-size", type=int, default=64)
    parser.add_argument("--skip-mnn-export", action="store_true")
    args = parser.parse_args()

    model_dir = pathlib.Path(args.model_dir)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    facts = model_facts(model_dir)
    checksums = {}
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json"):
        p = model_dir / name
        if p.exists():
            checksums[name] = sha256_file(p)
            shutil.copy2(p, out_dir / name)

    manifest = {
        **facts,
        "quantization": {"bits": args.bits, "group_size": args.group_size, "scheme": f"w{args.bits}a16_groupwise"},
        "checksums": checksums,
        "mnn_commit": "0bff03cbef43c783f44e41484b9f8a0b28bd758d",
    }
    (out_dir / "xqwen35_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    if not args.skip_mnn_export:
        export = pathlib.Path(args.mnn_dir) / "transformers" / "llm" / "export" / "llmexport.py"
        if not export.exists():
            raise FileNotFoundError(f"MNN export script not found: {export}")
        cmd = [
            sys.executable,
            str(export),
            "--path",
            str(model_dir),
            "--export",
            "mnn",
            "--hqq",
            "--dst_path",
            str(out_dir / "mnn_stock"),
        ]
        subprocess.check_call(cmd)
    print(json.dumps({"manifest": str(out_dir / "xqwen35_manifest.json"), "facts": facts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
import argparse
import json
import pathlib


REQUIRED = ("hf_repo", "hf_revision", "quantization", "checksums")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    args = parser.parse_args()
    path = pathlib.Path(args.manifest)
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        raise SystemExit(f"manifest missing keys: {missing}")
    if data["hf_repo"] != "Qwen/Qwen3.5-9B":
        raise SystemExit("manifest is not for Qwen/Qwen3.5-9B")
    if data["quantization"]["bits"] not in (2, 3, 4):
        raise SystemExit("unsupported quantization bitwidth")
    print(json.dumps({"ok": True, "manifest": str(path), "quantization": data["quantization"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
import argparse
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "generated" / "arm64_neon"


def run(script: str) -> None:
    subprocess.check_call([sys.executable, str(ROOT / "generator" / script)])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="generate into memory and report expected files")
    args = parser.parse_args()
    if args.check:
        for name in ("xq_gemv_w4a16_neon.cpp", "xq_gemv_w3a16_neon.cpp", "xq_gemv_w2a16_neon.cpp"):
            print(GEN / name)
        return 0
    run("gen_gemv_w4a16.py")
    run("gen_gemv_w3a16.py")
    run("gen_gemv_w2a16.py")
    run("gen_rmsnorm.py")
    run("gen_rope.py")
    run("gen_attention_decode.py")
    run("gen_gated_delta.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


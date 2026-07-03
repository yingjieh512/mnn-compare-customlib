#!/usr/bin/env python3
import argparse
import json
import math
import pathlib
from typing import Iterable, List, Tuple


def quantize_group(values: Iterable[float], bits: int) -> Tuple[List[int], float, float]:
    vals = list(values)
    qmax = (1 << bits) - 1
    mn = min(vals)
    mx = max(vals)
    if mx <= mn:
        return [0 for _ in vals], 1.0, 0.0
    scale = (mx - mn) / qmax
    zero = round(-mn / scale)
    codes = [max(0, min(qmax, int(round(v / scale + zero)))) for v in vals]
    return codes, scale, float(zero)


def pack_codes(codes: Iterable[int], bits: int) -> bytes:
    code_list = list(codes)
    out = bytearray((len(code_list) * bits + 7) // 8)
    for idx, code in enumerate(code_list):
        for b in range(bits):
            if (code >> b) & 1:
                bit = idx * bits + b
                out[bit >> 3] |= 1 << (bit & 7)
    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bits", type=int, choices=(2, 3, 4), required=True)
    parser.add_argument("--group-size", type=int, default=64)
    parser.add_argument("--describe", action="store_true")
    args = parser.parse_args()
    if args.describe:
        print(json.dumps({"scheme": f"w{args.bits}a16_groupwise", "group_size": args.group_size}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

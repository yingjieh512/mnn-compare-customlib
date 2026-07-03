#!/usr/bin/env python3
import argparse
import json
import pathlib


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_results")
    parser.add_argument("--out-md", default="results/reports/comparison.md")
    parser.add_argument("--out-json", default="results/reports/comparison.json")
    args = parser.parse_args()
    data = json.loads(pathlib.Path(args.parsed_results).read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    stock = summary.get("mnn_stock", {}).get("median_decode_tps", 0.0)
    custom = summary.get("customlib", {}).get("median_decode_tps", 0.0)
    speedup = custom / stock if stock > 0 else 0.0
    comparison = {
        "stock_mnn_decode_tps": stock,
        "customlib_decode_tps": custom,
        "speedup_ratio": speedup,
        "target_20_decode_tps_passed": custom >= 20.0,
    }
    pathlib.Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out_json).write_text(json.dumps(comparison, indent=2, sort_keys=True), encoding="utf-8")
    md = (
        "| Engine | Median decode tok/s |\n"
        "|---|---:|\n"
        f"| stock MNN | {stock:.4f} |\n"
        f"| customlib | {custom:.4f} |\n\n"
        f"Speedup: {speedup:.4f}x\n\n"
        f">=20 decode tok/s: {'PASS' if custom >= 20.0 else 'FAIL'}\n"
    )
    pathlib.Path(args.out_md).write_text(md, encoding="utf-8")
    print(json.dumps(comparison, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
import argparse
import json
import pathlib
import statistics
from typing import Any, Dict, Iterable, List


def load_json_objects(path: pathlib.Path) -> Iterable[Dict[str, Any]]:
    if path.suffix == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        yield item
            elif isinstance(data, dict):
                yield data
        except json.JSONDecodeError:
            pass
    text = path.read_text(encoding="utf-8", errors="ignore")
    marker = "BENCH_RESULT_JSON "
    for line in text.splitlines():
        idx = line.find(marker)
        if idx >= 0:
            try:
                yield json.loads(line[idx + len(marker):])
            except json.JSONDecodeError:
                continue


def p90(values: List[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    return values[min(len(values) - 1, int(0.9 * (len(values) - 1)))]


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    groups: Dict[str, List[float]] = {}
    for row in rows:
        engine = row.get("engine", "unknown")
        decode = row.get("tokens_per_second", {}).get("decode", 0.0)
        if isinstance(decode, (int, float)):
            groups.setdefault(engine, []).append(float(decode))
    summary = {}
    for engine, vals in groups.items():
        summary[engine] = {
            "runs": len(vals),
            "median_decode_tps": statistics.median(vals) if vals else 0.0,
            "min_decode_tps": min(vals) if vals else 0.0,
            "max_decode_tps": max(vals) if vals else 0.0,
            "p90_decode_tps": p90(vals),
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--out", default="results/reports/parsed_results.json")
    args = parser.parse_args()
    rows: List[Dict[str, Any]] = []
    for raw in args.paths:
        path = pathlib.Path(raw)
        files = [path] if path.is_file() else list(path.rglob("*"))
        for f in files:
            if f.is_file():
                rows.extend(load_json_objects(f))
    out = {"schema_version": 1, "runs": rows, "summary": summarize(rows)}
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(out["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


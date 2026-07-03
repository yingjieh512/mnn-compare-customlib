#!/usr/bin/env python3
import argparse
import json
import pathlib
import sys

from common import EXACT_MANUFACTURER, EXACT_MODEL, add_region_arg, aws, exact_device_matches, write_blocker


def main() -> int:
    parser = argparse.ArgumentParser()
    add_region_arg(parser)
    parser.add_argument("--out", default="results/raw/devicefarm_devices.json")
    args = parser.parse_args()

    try:
        data = aws(["devicefarm", "list-devices"], region=args.region)
    except Exception as exc:
        blocker = write_blocker("AWS Device Farm list-devices failed", {"error": str(exc)}, args.region)
        print(f"BLOCKED: wrote {blocker}", file=sys.stderr)
        return 2

    devices = data.get("devices", [])
    matches = [d for d in devices if exact_device_matches(d)]
    evidence = {
        "filter": {"manufacturer": EXACT_MANUFACTURER, "model": EXACT_MODEL},
        "match_count": len(matches),
        "matches": [
            {
                "arn": d.get("arn"),
                "name": d.get("name"),
                "manufacturer": d.get("manufacturer"),
                "model": d.get("model"),
                "os": d.get("os"),
                "availability": d.get("availability"),
                "fleetType": d.get("fleetType"),
            }
            for d in matches
        ],
    }
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps({"devices": devices, "exact_matches": matches}, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    if not matches:
        blocker = write_blocker("Exact Samsung Galaxy S26 Ultra unavailable in Device Farm list-devices output", evidence, args.region)
        print(f"BLOCKED: wrote {blocker}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


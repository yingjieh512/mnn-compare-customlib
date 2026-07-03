#!/usr/bin/env python3
import argparse
import json
import pathlib
import tempfile

from common import EXACT_MODEL, add_region_arg, aws, exact_device_matches


def main() -> int:
    parser = argparse.ArgumentParser()
    add_region_arg(parser)
    parser.add_argument("--project-arn", required=True)
    parser.add_argument("--device-arn", action="append")
    parser.add_argument("--name", default="exact-samsung-galaxy-s26-ultra")
    args = parser.parse_args()

    pools = aws(["devicefarm", "list-device-pools", "--arn", args.project_arn], region=args.region).get("devicePools", [])
    for pool in pools:
        if pool.get("name") == args.name:
            print(json.dumps(pool, indent=2))
            return 0

    device_arns = args.device_arn
    if not device_arns:
        devices = aws(["devicefarm", "list-devices"], region=args.region).get("devices", [])
        device_arns = [d["arn"] for d in devices if exact_device_matches(d)]
    if not device_arns:
        raise SystemExit(f"No exact {EXACT_MODEL} device ARN available")

    rules = [{"attribute": "ARN", "operator": "IN", "value": json.dumps(device_arns)}]
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f:
        json.dump(rules, f)
        rules_path = pathlib.Path(f.name)
    pool = aws(
        [
            "devicefarm",
            "create-device-pool",
            "--project-arn",
            args.project_arn,
            "--name",
            args.name,
            "--rules",
            f"file://{rules_path}",
        ],
        region=args.region,
    ).get("devicePool", {})
    print(json.dumps(pool, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


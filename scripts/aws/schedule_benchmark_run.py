#!/usr/bin/env python3
import argparse
import json

from common import add_region_arg, aws


def main() -> int:
    parser = argparse.ArgumentParser()
    add_region_arg(parser)
    parser.add_argument("--project-arn", required=True)
    parser.add_argument("--app-arn", required=True)
    parser.add_argument("--test-package-arn", required=True)
    parser.add_argument("--device-pool-arn", required=True)
    parser.add_argument("--name", default="qwen35-9b-stock-and-customlib")
    args = parser.parse_args()

    test_spec = f"type=INSTRUMENTATION,testPackageArn={args.test_package_arn}"
    run = aws(
        [
            "devicefarm",
            "schedule-run",
            "--project-arn",
            args.project_arn,
            "--app-arn",
            args.app_arn,
            "--device-pool-arn",
            args.device_pool_arn,
            "--name",
            args.name,
            "--test",
            test_spec,
        ],
        region=args.region,
    ).get("run", {})
    print(json.dumps(run, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


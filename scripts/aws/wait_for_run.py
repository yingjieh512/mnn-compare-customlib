#!/usr/bin/env python3
import argparse
import json
import time

from common import add_region_arg, aws


TERMINAL = {"COMPLETED", "ERRORED", "STOPPED"}


def main() -> int:
    parser = argparse.ArgumentParser()
    add_region_arg(parser)
    parser.add_argument("--run-arn", required=True)
    parser.add_argument("--poll-seconds", type=int, default=30)
    args = parser.parse_args()
    while True:
        run = aws(["devicefarm", "get-run", "--arn", args.run_arn], region=args.region).get("run", {})
        print(json.dumps({"status": run.get("status"), "result": run.get("result"), "arn": run.get("arn")}, indent=2))
        if run.get("status") in TERMINAL:
            print(json.dumps(run, indent=2))
            return 0 if run.get("result") == "PASSED" else 5
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())


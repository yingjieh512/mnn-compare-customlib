#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import sys

from common import DEFAULT_REGION, add_region_arg, aws, profile_names, redact_identity, write_blocker


def try_identity(region: str, profile):
    try:
        identity = aws(["sts", "get-caller-identity"], region=region, profile=profile)
        return identity, None
    except Exception as exc:
        return None, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    add_region_arg(parser)
    parser.add_argument("--out", default="results/raw/aws_identity.json")
    args = parser.parse_args()

    attempts = []
    identity, error = try_identity(args.region, None)
    attempts.append({"profile": os.environ.get("AWS_PROFILE", "environment/default"), "ok": identity is not None, "error": error})
    if identity:
        redacted = redact_identity(identity)
        pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.out).write_text(json.dumps(redacted, indent=2), encoding="utf-8")
        print(json.dumps(redacted, indent=2))
        return 0

    for profile in profile_names():
        identity, error = try_identity(args.region, profile)
        attempts.append({"profile": profile, "ok": identity is not None, "error": error})
        if identity:
            redacted = redact_identity(identity)
            pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(args.out).write_text(json.dumps(redacted, indent=2), encoding="utf-8")
            print(json.dumps(redacted, indent=2))
            return 0

    blocker = write_blocker("AWS credentials unavailable", {"attempts": attempts}, args.region)
    print(f"BLOCKED: AWS credentials unavailable. Wrote {blocker}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


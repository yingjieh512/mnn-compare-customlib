#!/usr/bin/env python3
import argparse
import json
import pathlib
import urllib.request

from common import add_region_arg, aws


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)[:180]


def main() -> int:
    parser = argparse.ArgumentParser()
    add_region_arg(parser)
    parser.add_argument("--run-arn", required=True)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()
    out_dir = pathlib.Path(args.out_dir or ("results/raw/" + safe_name(args.run_arn)))
    out_dir.mkdir(parents=True, exist_ok=True)

    all_artifacts = []
    for artifact_type in ("FILE", "LOG", "SCREENSHOT"):
        try:
            artifacts = aws(["devicefarm", "list-artifacts", "--arn", args.run_arn, "--type", artifact_type], region=args.region).get("artifacts", [])
        except Exception:
            artifacts = []
        for artifact in artifacts:
            all_artifacts.append(artifact)
            url = artifact.get("url")
            if not url:
                continue
            name = safe_name(artifact.get("name") or artifact.get("arn") or artifact_type)
            suffix = pathlib.Path(artifact.get("extension") or "").suffix
            target = out_dir / (name + (suffix if suffix else ""))
            with urllib.request.urlopen(url, timeout=120) as resp:
                target.write_bytes(resp.read())
    (out_dir / "artifacts.json").write_text(json.dumps(all_artifacts, indent=2), encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "artifact_count": len(all_artifacts)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


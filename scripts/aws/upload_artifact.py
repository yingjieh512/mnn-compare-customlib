#!/usr/bin/env python3
import argparse
import json
import mimetypes
import pathlib
import time
import urllib.request

from common import add_region_arg, aws


def redact_upload(upload):
    safe = dict(upload)
    url = safe.get("url")
    if isinstance(url, str) and "?" in url:
        safe["url"] = url.split("?", 1)[0] + "?REDACTED"
    return safe


def main() -> int:
    parser = argparse.ArgumentParser()
    add_region_arg(parser)
    parser.add_argument("--project-arn", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--type", required=True, help="ANDROID_APP, INSTRUMENTATION_TEST_PACKAGE, APPIUM_JAVA_JUNIT_TEST_PACKAGE, EXTERNAL_DATA, ...")
    parser.add_argument("--name")
    args = parser.parse_args()

    path = pathlib.Path(args.path)
    content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    upload = aws(
        [
            "devicefarm",
            "create-upload",
            "--project-arn",
            args.project_arn,
            "--name",
            args.name or path.name,
            "--type",
            args.type,
            "--content-type",
            content_type,
        ],
        region=args.region,
    ).get("upload", {})
    url = upload["url"]
    req = urllib.request.Request(url, data=path.read_bytes(), method="PUT", headers={"Content-Type": content_type})
    with urllib.request.urlopen(req, timeout=300) as resp:
        resp.read()

    arn = upload["arn"]
    for _ in range(60):
        cur = aws(["devicefarm", "get-upload", "--arn", arn], region=args.region).get("upload", {})
        if cur.get("status") in ("SUCCEEDED", "FAILED"):
            print(json.dumps(redact_upload(cur), indent=2))
            return 0 if cur.get("status") == "SUCCEEDED" else 4
        time.sleep(5)
    raise SystemExit("Timed out waiting for Device Farm upload processing")


if __name__ == "__main__":
    raise SystemExit(main())

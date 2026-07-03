#!/usr/bin/env python3
import argparse
import json

from common import add_region_arg, aws


PROJECT_NAME = "qwen35-9b-customlib-bench"


def main() -> int:
    parser = argparse.ArgumentParser()
    add_region_arg(parser)
    parser.add_argument("--name", default=PROJECT_NAME)
    args = parser.parse_args()

    projects = aws(["devicefarm", "list-projects"], region=args.region).get("projects", [])
    for project in projects:
        if project.get("name") == args.name:
            print(json.dumps(project, indent=2))
            return 0
    project = aws(["devicefarm", "create-project", "--name", args.name], region=args.region).get("project", {})
    print(json.dumps(project, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


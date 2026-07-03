#!/usr/bin/env python3
import argparse
import configparser
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Any, Dict, Iterable, List, Optional


ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-west-2"
EXACT_MANUFACTURER = "Samsung"
EXACT_MODEL = "Galaxy S26 Ultra"


def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    if cmd and cmd[0] == "aws":
        aws_exe = shutil.which("aws") or shutil.which("aws.cmd") or shutil.which("aws.exe")
        if aws_exe:
            cmd = [aws_exe] + cmd[1:]
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(detail or f"command failed with exit code {proc.returncode}: {cmd[0]}")
    return proc


def aws(args: List[str], region: str = DEFAULT_REGION, profile: Optional[str] = None, check: bool = True) -> Dict[str, Any]:
    profiles: List[Optional[str]] = [profile]
    if profile is None and args[:2] != ["sts", "get-caller-identity"]:
        profiles.extend(p for p in profile_names() if p)
    errors = []
    for candidate in profiles:
        cmd = ["aws"]
        if candidate:
            cmd += ["--profile", candidate]
        cmd += ["--region", region] + args + ["--output", "json"]
        try:
            proc = run(cmd, check=check)
            if not proc.stdout.strip():
                return {}
            return json.loads(proc.stdout)
        except Exception as exc:
            errors.append({"profile": candidate or "environment/default", "error": str(exc)})
            if profile is not None:
                break
    raise RuntimeError(json.dumps({"aws_call_failed": args, "attempts": errors}, indent=2))


def profile_names() -> List[str]:
    names = []
    env_profile = os.environ.get("AWS_PROFILE")
    if env_profile:
        names.append(env_profile)

    config_paths = [pathlib.Path.home() / ".aws" / "config", pathlib.Path.home() / ".aws" / "credentials"]
    parser = configparser.ConfigParser()
    parser.read([str(p) for p in config_paths if p.exists()])
    for section in parser.sections():
        name = section
        if name.startswith("profile "):
            name = name[len("profile "):]
        if name not in names:
            names.append(name)

    for plausible in ("default", "devicefarm", "mobile", "benchmark", "qwen", "qwen-bench"):
        if plausible not in names:
            names.append(plausible)
    return names


def redact_identity(identity: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Account": identity.get("Account", ""),
        "Arn": "REDACTED" if identity.get("Arn") else "",
        "UserId": "REDACTED" if identity.get("UserId") else "",
    }


def write_blocker(reason: str, evidence: Dict[str, Any], region: str = DEFAULT_REGION) -> pathlib.Path:
    out = ROOT / "results" / "devicefarm_blocker.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    body = [
        "# AWS Device Farm Blocker",
        "",
        f"- timestamp_utc: `{now}`",
        f"- region: `{region}`",
        f"- exact_manufacturer_filter: `{EXACT_MANUFACTURER}`",
        f"- exact_model_filter: `{EXACT_MODEL}`",
        f"- reason: `{reason}`",
        "",
        "## Evidence",
        "",
        "```json",
        json.dumps(evidence, indent=2, sort_keys=True),
        "```",
        "",
        "## Next Action",
        "",
        "Provide AWS credentials with Device Farm access in the default credential chain or set AWS_PROFILE, then rerun `scripts/aws/list_devicefarm_devices.py --region us-west-2`.",
        "",
    ]
    out.write_text("\n".join(body), encoding="utf-8")
    return out


def add_region_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--region", default=DEFAULT_REGION)


def exact_device_matches(device: Dict[str, Any]) -> bool:
    manufacturer = str(device.get("manufacturer", "")).lower()
    name = str(device.get("name", "")).lower()
    model = str(device.get("model", "")).lower()
    return manufacturer == EXACT_MANUFACTURER.lower() and (
        name == EXACT_MODEL.lower() or model == EXACT_MODEL.lower() or EXACT_MODEL.lower() in name
    )

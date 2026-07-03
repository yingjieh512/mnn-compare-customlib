#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -z "${ANDROID_HOME:-}" && -d "${LOCALAPPDATA:-}/Android/Sdk" ]]; then
  export ANDROID_HOME="${LOCALAPPDATA}/Android/Sdk"
fi

if [[ -z "${ANDROID_NDK_HOME:-}" && -n "${ANDROID_HOME:-}" ]]; then
  export ANDROID_NDK_HOME="$(find "$ANDROID_HOME/ndk" -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)"
fi

if [[ -x "./gradlew" ]]; then
  GRADLE=("./gradlew")
elif command -v gradle >/dev/null 2>&1; then
  GRADLE=("gradle")
else
  echo "No gradle or gradlew found. Run scripts/bootstrap_gradle.ps1 on Windows or install Gradle 8.7." >&2
  exit 2
fi

"${GRADLE[@]}" \
  :stock_mnn_benchmark:assembleDebug \
  :stock_mnn_benchmark:assembleRelease \
  :stock_mnn_benchmark:assembleAndroidTest \
  :customlib_benchmark:assembleDebug \
  :customlib_benchmark:assembleRelease \
  :customlib_benchmark:assembleAndroidTest

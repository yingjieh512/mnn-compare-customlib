#!/usr/bin/env bash
set -euo pipefail

ADB="${ADB:-adb}"
"$ADB" shell getprop ro.product.manufacturer
"$ADB" shell getprop ro.product.model
"$ADB" shell getprop ro.product.device
"$ADB" shell getprop ro.hardware
"$ADB" shell getprop ro.board.platform
"$ADB" shell dumpsys thermalservice || true
"$ADB" shell dumpsys battery || true
"$ADB" logcat -c
"$ADB" shell am instrument -w com.example.xqwen35bench.test/androidx.test.runner.AndroidJUnitRunner
"$ADB" logcat -d | grep BENCH_RESULT_JSON || true


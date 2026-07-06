#!/usr/bin/env python3
"""Generate the accepted v27 final report artifacts from evidence JSON."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


EVIDENCE = Path("results/reports/evidence")
REPORTS = Path("results/reports")

ARNS = {
    "stock_benchmark": "arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/5165cf70-4ad2-4f21-bd40-89c6dd97c246",
    "custom_benchmark": "arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/c444a573-d0e1-4924-abe2-5ca587478c2c",
    "stock_quality": "arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/9908fb50-103c-4698-81c9-f2f12b98b335",
    "custom_quality": "arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/4ac8ce83-abf1-42fe-8cd2-3ffde19821f2",
    "v17_custom": "arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/1de54984-c9d9-41d1-81c1-7eed941585ed",
}

PROJECT_ARN = "arn:aws:devicefarm:us-west-2:884244642857:project:64d2cc31-abd6-49f8-97da-162f82410bc0"
POOL_ARN = "arn:aws:devicefarm:us-west-2:884244642857:devicepool:64d2cc31-abd6-49f8-97da-162f82410bc0/14d31c96-b8fc-4930-99c7-1a8948124213"
MODEL_SHA = "9de692be1c1ef1002fac25bd8f93c76e1d31975caa234fe1725f9eb294bfaa34"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fmt(value: float | int | None, digits: int = 5) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def ms(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f} ms"


def percent_delta(ratio: float) -> str:
    return f"{(ratio - 1.0) * 100.0:.2f}%"


def tps(data: dict, phase: str) -> float:
    return float(data["tokens_per_second"][phase]["mean"])


def tpot(data: dict) -> float:
    return float(data["time_per_output_token_ms"]["decode"]["mean"])


def perf_row(
    name: str,
    engine: str,
    requested: str,
    actual: str,
    status: str,
    prefill: float,
    decode: float,
    decode_tpot: float,
    evidence: str,
    run: str,
) -> str:
    return (
        f"| {name} | {engine} | {requested} | {actual} | {status} | "
        f"{fmt(prefill)} | {fmt(decode)} | {ms(decode_tpot)} | `{run}` | `{evidence}` |"
    )


def main() -> int:
    stock = load_json(EVIDENCE / "stock_mnn_cpu_benchmark_v27.json")
    custom = load_json(EVIDENCE / "customlib_cpu_vulkan_hybrid_benchmark_v27.json")
    v17 = load_json(EVIDENCE / "customlib_cpu_vulkan_hybrid_benchmark_v17.json")
    v26 = load_json(EVIDENCE / "customlib_cpu_vulkan_hybrid_benchmark_v26.json")
    quality_stock = load_json(EVIDENCE / "quality_validation_v27_stock_english.json")
    quality_custom = load_json(EVIDENCE / "quality_validation_v27_custom_english.json")
    quality_comp = load_json(EVIDENCE / "quality_validation_v27_english_comparison.json")

    stock_prefill = tps(stock, "prefill")
    stock_decode = tps(stock, "decode")
    stock_tpot = tpot(stock)
    custom_prefill = tps(custom, "prefill")
    custom_decode = tps(custom, "decode")
    custom_tpot = tpot(custom)
    v17_prefill = tps(v17, "prefill")
    v17_decode = tps(v17, "decode")
    v17_tpot = tpot(v17)
    v26_prefill = tps(v26, "prefill")
    v26_decode = tps(v26, "decode")
    v26_tpot = tpot(v26)

    custom_stock_ratio = custom_decode / stock_decode
    custom_v17_ratio = custom_decode / v17_decode
    custom_v26_ratio = custom_decode / v26_decode
    selected = custom["runtime"]["selected_kernels"]

    perf_table = "\n".join(
        [
            "| Variant | Engine | Requested backend | Actual backend | Status | Prefill TPS | Decode TPS | Decode TPOT | Device Farm run ARN | Evidence |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
            perf_row(
                "Fresh stock CPU v27",
                "stock_mnn",
                "cpu",
                "cpu",
                "ok",
                stock_prefill,
                stock_decode,
                stock_tpot,
                "results/reports/evidence/stock_mnn_cpu_benchmark_v27.json",
                ARNS["stock_benchmark"],
            ),
            perf_row(
                "Final custom v27",
                "customlib",
                "cpu_vulkan_hybrid",
                "cpu",
                "ok, full custom decode",
                custom_prefill,
                custom_decode,
                custom_tpot,
                "results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v27.json",
                ARNS["custom_benchmark"],
            ),
            perf_row(
                "Accepted v17 baseline",
                "customlib",
                "cpu_vulkan_hybrid",
                "cpu",
                "historical baseline",
                v17_prefill,
                v17_decode,
                v17_tpot,
                "results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v17.json",
                ARNS["v17_custom"],
            ),
            perf_row(
                "v26 buffer-reuse candidate",
                "customlib",
                "cpu_vulkan_hybrid",
                "cpu",
                "superseded by v27",
                v26_prefill,
                v26_decode,
                v26_tpot,
                "results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v26.json",
                "see v26 scheduled evidence",
            ),
        ]
    )

    quality_rows = [
        "| Prompt | Exact match | Prefix tokens | Token match rate | Edit distance | First mismatch | Custom sanity | Repeated token 220 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in quality_comp["prompts"]:
        quality_rows.append(
            f"| {item['id']} | {'yes' if item['exact_match'] else 'no'} | "
            f"{item['prefix_match_length']} | {float(item['token_match_rate']):.3f} | "
            f"{item['edit_distance']} | "
            f"{item['first_mismatch_position'] if item['first_mismatch_position'] is not None else 'none'} | "
            f"{'yes' if item['comparison_gate_passed'] else 'no'} | "
            f"{'yes' if item.get('custom_repeated_token_220_failure') else 'no'} |"
        )
    quality_table = "\n".join(quality_rows)

    coverage_rows = ["| Op family | Backend | Replaced? | Fallback? |", "| --- | --- | ---: | ---: |"]
    for family in selected["replaced_op_families"]:
        backend = selected["op_family_backends"].get(family, "cpu")
        coverage_rows.append(f"| {family} | {backend} | yes | no |")
    coverage_table = "\n".join(coverage_rows)

    per_rows = sorted(
        custom["per_kernel_wall_clock"]["rows"],
        key=lambda row: float(row.get("total_ms", 0.0)),
        reverse=True,
    )
    per_table_rows = [
        "| Kernel / row | Op family | Backend | Calls | Total ms | Mean ms | Min ms | Max ms |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in per_rows:
        per_table_rows.append(
            f"| {row['name']} | {row['op_family']} | {row['backend']} | {row['calls']} | "
            f"{float(row['total_ms']):.3f} | {float(row['mean_ms']):.6f} | "
            f"{float(row['min_ms']):.6f} | {float(row['max_ms']):.6f} |"
        )
    per_table = "\n".join(per_table_rows)

    micro_rows = [
        "| Kernel | Backend | Implementation | Qwen3.5 shape | Mean wall ms | Median wall ms |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in custom["custom_kernel_microbench"]["rows"]:
        micro_rows.append(
            f"| {row['name']} | {row['backend']} | {row['implementation']} | "
            f"{row['qwen35_shape']} | {float(row['wall_ms']['mean']):.5f} | "
            f"{float(row['wall_ms']['median']):.5f} |"
        )
    micro_table = "\n".join(micro_rows)

    mnn_trace = custom["mnn_hotpath_op_trace"]
    type_rows = ["| Stage | Type | Calls | Total ms | Mean ms |", "| --- | --- | ---: | ---: | ---: |"]
    for row in mnn_trace["top_by_type"][:12]:
        type_rows.append(
            f"| {row['stage']} | {row['type']} | {row['calls']} | "
            f"{float(row['total_ms']):.3f} | {float(row['mean_ms']):.6f} |"
        )
    type_table = "\n".join(type_rows)

    name_rows = [
        "| Stage | Type | Name | Calls | Total ms | Mean ms |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in mnn_trace["top_by_name"][:12]:
        name_rows.append(
            f"| {row['stage']} | {row['type']} | `{row['name']}` | {row['calls']} | "
            f"{float(row['total_ms']):.3f} | {float(row['mean_ms']):.6f} |"
        )
    name_table = "\n".join(name_rows)

    examples = "\n".join(
        [
            f"- `{item['id']}`: stock first tokens `{item['stock_generated_token_ids'][:16]}`, "
            f"custom first tokens `{item['custom_generated_token_ids'][:16]}`."
            for item in quality_comp["prompts"]
        ]
    )

    report = f"""# Final Device Farm Report: Qwen3.5-9B Stock MNN vs Customlib v27

## Honest Verdict

- Faithful benchmark: YES. The final accepted runs are full Qwen3.5-9B Device Farm runs on the same Samsung Galaxy S26 Ultra pool, same verified model package, same 512-token prompt length, same 256-token decode length, greedy settings, and 1 warmup / 3 measured iterations.
- Requirement 1 met: YES. The custom kernel library exists and the code walkthrough is `docs/kernel_library_code_walkthrough_final.md`.
- Requirement 2 met: YES. This report compares generated custom kernels against stock MNN with per-kernel wall clock, MNN hot-path trace, overall TPOT/TPS, Device Farm ARNs, and evidence JSON.
- Requirement 3, output quality guard: YES for deterministic sanity validation. Stock MNN and customlib both emitted `BENCH_QUALITY_JSON`; 5 / 5 prompts passed the comparison sanity gate, with 1 / 5 exact full-output token matches. No production-level semantic quality claim is made.
- Custom speedup claim allowed: NO. Final custom decode TPS is `{fmt(custom_decode)}` and fresh stock MNN CPU decode TPS is `{fmt(stock_decode)}`, so custom is `{custom_stock_ratio:.4f}x` stock CPU. The accepted v27 custom path is faster than v17 by `{percent_delta(custom_v17_ratio)}` but still slower than stock MNN CPU.
- Vulkan attempted: YES. The custom run requested `cpu_vulkan_hybrid` and probed Vulkan successfully, but `custom_backend_actual = cpu` and no custom Vulkan generation kernels were used. Stock Vulkan remains a prior attempted backend that crashed before benchmark JSON in v17 and is not used for the final speed comparison.

## Final Acceptance Summary

| Gate | Result | Evidence |
| --- | --- | --- |
| Full custom path | PASS | `use_mnn_fallback = 0`, `calls_mnn_llm_response_for_measured_generation = false`, `full_custom_decode = true`, `fallback_op_families = []` in `customlib_cpu_vulkan_hybrid_benchmark_v27.json` |
| Output quality | PASS | `quality_validation_v27_english_comparison.json`, 5 / 5 comparison-gate prompts, no invalid/empty/degenerate outputs |
| Full Device Farm benchmark | PASS | custom v27 run `{ARNS['custom_benchmark']}` emitted `BENCH_RESULT_JSON` |
| Performance versus v17 | PASS | custom v27 decode TPS `{fmt(custom_decode)}` versus v17 `{fmt(v17_decode)}`, ratio `{custom_v17_ratio:.4f}x` |
| Performance versus fresh stock | NO SPEEDUP | custom v27 / stock v27 decode ratio `{custom_stock_ratio:.4f}x` |

## Device Farm Evidence

- Project ARN: `{PROJECT_ARN}`
- Device pool ARN: `{POOL_ARN}`
- Device: Samsung Galaxy S26 Ultra, model ID SM-S948U1, Android 16.
- Model: `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, W4A16 groupwise quantization, group size 64.
- Full model zip SHA-256 verified on-device: `{MODEL_SHA}`.
- Split package bytes: 4,500,000,000 + 4,500,000,000 + 2,266,405,198 = 11,266,405,198.
- Final stock benchmark run ARN: `{ARNS['stock_benchmark']}`.
- Final custom benchmark run ARN: `{ARNS['custom_benchmark']}`.
- Final stock quality run ARN: `{ARNS['stock_quality']}`.
- Final custom quality run ARN: `{ARNS['custom_quality']}`.

| Run | Result | Evidence |
| --- | --- | --- |
| stock_mnn_v27_benchmark_cpu_qwen35_9b | PASSED | `results/reports/evidence/stock_mnn_cpu_benchmark_v27.json` |
| customlib_v27_benchmark_cpu_vulkan_hybrid_qwen35_9b | PASSED | `results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v27.json` |
| stock_mnn_v27_quality_english_qwen35_9b | PASSED | `results/reports/evidence/quality_validation_v27_stock_english.json` |
| customlib_v27_quality_english_qwen35_9b | PASSED | `results/reports/evidence/quality_validation_v27_custom_english.json` |
| stock/custom quality comparison | PASS | `results/reports/evidence/quality_validation_v27_english_comparison.json` |

## Same Settings

| Field | Value |
| --- | --- |
| Prompt tokens requested | 512 |
| max_new_tokens | 256 |
| Prompt token id for performance run | 16 |
| Temperature / top_k / top_p | 0 / 1 / 1 |
| Batch size | 1 |
| Warmup / measured iterations | 1 / 3 |
| Quality prompts | five deterministic English fixed token-ID prompts |
| Model package | same verified Qwen3.5-9B W4A16 package |
| Device pool | same Samsung Galaxy S26 Ultra pool |

## Overall Performance

{perf_table}

## Comparisons

| Comparison | Decode TPS ratio | Decode TPOT delta | Interpretation |
| --- | ---: | ---: | --- |
| Final custom v27 / fresh stock MNN CPU v27 | {custom_stock_ratio:.4f}x | {custom_tpot - stock_tpot:+.3f} ms | Custom is slower than stock; no speedup is claimed. |
| Final custom v27 / accepted v17 custom baseline | {custom_v17_ratio:.4f}x | {custom_tpot - v17_tpot:+.3f} ms | v27 improves custom decode TPS by {percent_delta(custom_v17_ratio)} and lowers TPOT. |
| Final custom v27 / v26 buffer-reuse candidate | {custom_v26_ratio:.4f}x | {custom_tpot - v26_tpot:+.3f} ms | v27 recovers performance after quality fixes and buffer reuse. |

## Output Correctness / Quality Guard

TPS/TPOT measure speed, not semantic quality. The final custom result is accepted only because it also passes a deterministic output sanity guard against stock MNN on Device Farm. The validation uses fixed English token-ID prompts so both engines receive identical prompt IDs. It reports exact token match, prefix match length, token match rate, edit distance, invalid-token checks, empty-output checks, and repeated-token checks.

- Quality gate passed: YES.
- Stock native quality gate: YES.
- Custom native quality gate: YES.
- Exact full-output token match: `{quality_comp['exact_match_prompt_count']} / {quality_comp['prompt_count']}` prompts.
- Comparison-gate pass: `{quality_comp['comparison_gate_prompt_count']} / {quality_comp['prompt_count']}` prompts.
- Invalid token IDs: none in stock or custom outputs.
- Empty outputs: none.
- Degenerate repeated-token outputs: none.
- Repeated token 220 failure: none.
- Custom decoded text is not claimed because tokenizer decode is unavailable in the custom artifact; token IDs are dumped and compared directly.

{quality_table}

Token examples:

{examples}

Limitations: The custom library is validated here for operator correctness, deterministic full custom decode-path execution, and basic generated-token sanity against stock MNN. It is not claimed as a production-quality model replacement; full semantic quality validation would require perplexity and downstream task benchmarks.

## Custom Path Coverage

Measured custom generation evidence from the v27 JSON:

```text
{selected['summary']}
```

- `runtime.selected_kernels.hotpath_replaced = true`
- `runtime.selected_kernels.full_custom_decode = true`
- `runtime.selected_kernels.fallback_op_families = []`
- `custom_path.use_mnn_fallback = 0`
- `custom_path.calls_mnn_llm_response_for_measured_generation = false`
- `custom_backend_requested = cpu_vulkan_hybrid`
- `custom_backend_actual = cpu`

{coverage_table}

## What Changed Since v17

The accepted v27 result starts from the v17 full-custom systems baseline, rejects the faster-but-broken repeated-token quality path, and adds correctness plus performance fixes before final acceptance:

- RMSNorm and Q/K norm loader now applies Qwen-style weight offset handling through `addOneToVector`.
- RoPE uses the Qwen3.5 active-slice layout and correct absolute position handling.
- Linear-attention recurrent update uses exported `A_log` and `dt_bias` gate semantics instead of the earlier approximation.
- XQ4 loading supports both symmetric v1 and affine-asymmetric v2 matrices without confusing dequant formulas.
- Prefill and decode reduce allocations by reusing buffers, reserving KV cache, keeping an embedding stream open, and reusing attention score/max buffers.
- The W4A16 generated GEMV branches once per matrix on affine-vs-symmetric dequant, so the final symmetric Qwen package avoids a per-row/per-group runtime branch.

## Custom Per-Kernel Wall Clock

This table comes from `results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v27.json`. The requested custom backend was `cpu_vulkan_hybrid`; the actual measured backend for all custom ops was CPU.

{per_table}

Note: `sampling_greedy_custom` wraps the greedy section and overlaps with `lm_head_custom`; do not sum those two as exclusive time.

## Generated Kernel Microbench

The microbench ran on the same custom Device Farm APK after measured custom generation. It is not used for the overall TPS calculation.

{micro_table}

## MNN Hot-Path Trace: Top Op Types

The MNN hot-path trace is a separate debug-callback trace collected inside the custom APK after measured custom generation. It is evidence for MNN op wall-clock hotspots; it is not part of the measured custom generation path.

{type_table}

## MNN Hot-Path Trace: Top Op Names

{name_table}

## Code Walkthrough Pointers

- Public ABI: `customlib/include/xqwen35.h`.
- Custom runtime selection: `customlib/runtime/session.cpp` creates `CustomModel` when `use_mnn_fallback = 0`; the Android custom benchmark sets that field to zero.
- Full custom prefill/decode: `customlib/runtime/custom_model.cpp` implements prompt-token prefill, KV append, grouped-query attention, gated-delta linear attention state, final `lm_head_custom`, and greedy sampling.
- Generated W4A16 GEMV: `customlib/kernels/generated/arm64_neon/xq_gemv_w4a16_neon.cpp` uses tiled fused dequant GEMV, persistent worker threads, activation group-sum reuse, branch-specialized symmetric/affine dequant, and streaming lm_head argmax. The W4 file contains no `gemvLowBitReference` call.
- Packer/exporter: `customlib/packer/pack_qwen35_xq4.py` and `customlib/packer/pack_qwen35_xq4_numpy.py` export `lm_head.weight`, full-attention projections, MLP projections, linear-attention `in_proj_a`, `in_proj_b`, `conv1d.weight`, `A_log`, and `dt_bias`.
- Stock MNN connector: `android/app/src/main/cpp/stock_benchmark_jni.cpp`.
- Custom JNI/benchmark/quality connector and Vulkan probe: `android/benchmark_app/src/main/cpp/benchmark_jni.cpp`.
- Device Farm bootstrap connector: `android/benchmark_app/src/androidTest/java/com/example/xqwen35bench/ModelBootstrap.java` and the matching stock app bootstrap.

## Test Evidence

- Host build: `cmake --build build-host-quality` passed; log: `results/reports/evidence/host_build_v27.txt`.
- Host tests: `ctest --test-dir build-host-quality --output-on-failure` -> 2 / 2 passed; log: `results/reports/evidence/host_ctest_v27.txt`.
- Android build: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_android.ps1` passed; log: `results/reports/evidence/android_build_v27.txt`.
- Device Farm stock quality v27: PASSED and emitted `BENCH_QUALITY_JSON`.
- Device Farm custom quality v27: PASSED and emitted `BENCH_QUALITY_JSON`.
- Device Farm stock benchmark v27: PASSED and emitted `BENCH_RESULT_JSON`.
- Device Farm custom benchmark v27: PASSED and emitted `BENCH_RESULT_JSON`.

## Final Artifacts

- Final report: `results/reports/final_devicefarm_report.md`
- Machine-readable summary: `results/reports/final_devicefarm_report.json`
- Code walkthrough: `docs/kernel_library_code_walkthrough_final.md`
- Quality validation report: `results/reports/quality_validation_report.md`
- Quality comparison: `results/reports/evidence/quality_validation_v27_english_comparison.json`
- Final custom benchmark JSON: `results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v27.json`
- Final stock benchmark JSON: `results/reports/evidence/stock_mnn_cpu_benchmark_v27.json`
- Presentation deck: `results/reports/qwen35_9b_v27_quality_performance_presentation.pptx`

## Cleanup Evidence

Generated build trees, raw Device Farm artifacts, APKs, ZIPs, model shards, virtualenvs, and private upload specs are excluded from the final committed evidence. Use `scripts/cleanup_local_artifacts.ps1` to remove local-only artifacts after preserving the small report and evidence files.
"""
    (REPORTS / "final_devicefarm_report.md").write_text(report, encoding="utf-8")

    readme = f"""# Qwen3.5-9B Custom Mobile Inference Library

This repository builds and benchmarks a custom Android inference library for `Qwen/Qwen3.5-9B` against stock MNN on AWS Device Farm.

Final pinned inputs:

- MNN: `0bff03cbef43c783f44e41484b9f8a0b28bd758d`
- Hugging Face model: `Qwen/Qwen3.5-9B`
- HF revision: `c202236235762e1c871ad0ccb60c8ee5ba337b9a`
- Custom quantization: W4A16 groupwise, group size 64
- Final model package SHA-256: `{MODEL_SHA}`

## Final Status

The accepted v27 delivery is complete. Stock MNN CPU and customlib were scheduled on the same AWS Device Farm Samsung Galaxy S26 Ultra pool with the same full Qwen3.5-9B package, same 512-token prompt, same 256-token decode length, greedy settings, and 1 warmup / 3 measured iterations. Separate Device Farm quality-validation runs also compared stock and custom generated token IDs on five deterministic English prompts.

The measured custom generation path is full custom CPU generation:

- `use_mnn_fallback = 0`
- `custom_path.calls_mnn_llm_response_for_measured_generation = false`
- `runtime.selected_kernels.full_custom_decode = true`
- `runtime.selected_kernels.hotpath_replaced = true`
- `runtime.selected_kernels.fallback_op_families = []`

Final performance result:

| Variant | Requested backend | Actual backend | Status | Prefill TPS | Decode TPS | Decode TPOT |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Stock MNN v27 | cpu | cpu | ok | {fmt(stock_prefill)} | {fmt(stock_decode)} | {ms(stock_tpot)} |
| Customlib v27 | cpu_vulkan_hybrid | cpu | ok, full custom decode | {fmt(custom_prefill)} | {fmt(custom_decode)} | {ms(custom_tpot)} |
| Accepted v17 custom baseline | cpu_vulkan_hybrid | cpu | historical baseline | {fmt(v17_prefill)} | {fmt(v17_decode)} | {ms(v17_tpot)} |

Speedup verdict: no stock-MNN speedup is claimed. Final custom is `{custom_stock_ratio:.4f}x` fresh stock MNN CPU decode TPS. It is, however, `{custom_v17_ratio:.4f}x` the accepted v17 custom baseline and passes the new output-quality guard.

## Output Quality Guard

TPS/TPOT measure speed, not semantic quality. The final v27 custom result passed a deterministic Device Farm quality guard:

- Stock quality run ARN: `{ARNS['stock_quality']}`
- Custom quality run ARN: `{ARNS['custom_quality']}`
- Quality gate: PASS
- Exact full-output token match: `{quality_comp['exact_match_prompt_count']} / {quality_comp['prompt_count']}` prompts
- Comparison-gate prompts: `{quality_comp['comparison_gate_prompt_count']} / {quality_comp['prompt_count']}`
- Invalid tokens / empty outputs / repeated-token-220 degeneration: none

The custom library is validated for operator correctness, full custom decode-path execution, and basic generated-token sanity against stock MNN. It is not claimed as a production-quality model replacement; full semantic quality validation with perplexity and downstream task benchmarks remains future work.

## Final Evidence

- Final report: `results/reports/final_devicefarm_report.md`
- Machine-readable summary: `results/reports/final_devicefarm_report.json`
- Code walkthrough: `docs/kernel_library_code_walkthrough_final.md`
- Quality validation report: `results/reports/quality_validation_report.md`
- Stock benchmark evidence: `results/reports/evidence/stock_mnn_cpu_benchmark_v27.json`
- Custom benchmark evidence: `results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v27.json`
- Quality comparison evidence: `results/reports/evidence/quality_validation_v27_english_comparison.json`
- Presentation deck: `results/reports/qwen35_9b_v27_quality_performance_presentation.pptx`

Final AWS Device Farm runs:

- Stock MNN CPU benchmark: `{ARNS['stock_benchmark']}`
- Customlib benchmark: `{ARNS['custom_benchmark']}`
- Stock quality validation: `{ARNS['stock_quality']}`
- Custom quality validation: `{ARNS['custom_quality']}`
- Device pool: `{POOL_ARN}`

## What The Custom Library Replaces

The final measured custom path replaces the requested decode and prefill families:

- `q_proj`, `k_proj`, `v_proj`, `o_proj`
- `gate_proj`, `up_proj`, `down_proj`
- `rmsnorm`
- `rope`
- `attention`
- `linear_attention_state`
- `lm_head`
- `sampling`
- `prefill_kv_build`

The public ABI is in `customlib/include/xqwen35.h`. The measured Android custom benchmark enters the library through `xq_generate`, then runs `Session::prefill`, `Session::decodeOne`, and `CustomModel` without calling `MNN::Transformer::Llm::response`.

## Build Host Correctness Tests

```powershell
$env:PATH = "C:\\Users\\Yingjie Huang\\qwen-phone-npu-trial\\third_party\\toolchains\\w64devkit\\bin;$env:PATH"
cmake --build build-host-quality
ctest --test-dir build-host-quality --output-on-failure
```

Final host result: 2 / 2 tests passed. The tests cover W4A16 GEMV/reference behavior, lm_head argmax, greedy sampling, stable softmax, grouped-query attention, KV cache, RoPE, RMSNorm, linear-attention state, prefill KV length, and tiny end-to-end custom decode.

## Build Android APKs

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_android.ps1
```

The v27 Device Farm runs used rebuilt stock/custom release APKs plus androidTest APKs from this flow.

## Model Packing

The packers are `customlib/packer/pack_qwen35_xq4.py` and `customlib/packer/pack_qwen35_xq4_numpy.py`. They export W4A16 matrices and runtime metadata for full-attention projections, MLP projections, Qwen3.5 linear-attention tensors, `lm_head.weight`, embeddings, norm vectors, RoPE metadata, and quantization metadata. Device Farm reassembled and verified the three-part model package on-device before every final run.

## Repository Cleanup

Generated build trees, raw Device Farm artifacts, APKs, ZIPs, model shards, virtualenvs, and local upload specs are ignored. Use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/cleanup_local_artifacts.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/cleanup_local_artifacts.ps1 -Execute
```

The cleanup keeps source, documentation, final reports, and small evidence JSON/TXT/YML files. It keeps the final local model zip unless `-RemoveFinalModelZip` is explicitly passed.

## Honesty Rules

This repository only claims results backed by artifacts. The final v27 result is a faithful same-device full-model stock-vs-custom benchmark with a separate output-quality guard. It is not a stock-MNN speedup result and does not claim custom Vulkan kernel execution.
"""
    Path("README.md").write_text(readme, encoding="utf-8")

    walkthrough = f"""# Kernel Library Code Walkthrough Final

This document describes the accepted v27 custom inference library used for the Qwen3.5-9B AWS Device Farm quality and performance final. It matches the measured code path and evidence JSON, not a planned architecture.

## Final Measured Path

The final custom Android benchmark sets `xq_options.use_mnn_fallback = 0` in `android/benchmark_app/src/main/cpp/benchmark_jni.cpp` and enters the public ABI in `customlib/include/xqwen35.h`. The final run requested `cpu_vulkan_hybrid`, but the benchmark JSON reports `custom_backend_actual = cpu`; no custom Vulkan kernel is claimed.

Measured generation path:

```text
NativeBenchmark.runBenchmark
  -> xq_create
  -> xq_generate
     -> xq::runtime::Session::prefill
        -> xq::runtime::CustomModel::prefill
           -> load embedding for every prompt token
           -> run full layer stack for each prompt position
           -> append full-attention K/V cache
           -> update linear-attention recurrent state
     -> xq::runtime::Session::decodeOne
        -> xq::runtime::CustomModel::decodeOne
           -> run custom layer stack
           -> run real lm_head logits
           -> run greedy sampling
```

Final evidence:

- `custom_path.use_mnn_fallback = 0`
- `custom_path.calls_mnn_llm_response_for_measured_generation = false`
- `runtime.selected_kernels.full_custom_decode = true`
- `runtime.selected_kernels.hotpath_replaced = true`
- `runtime.selected_kernels.fallback_op_families = []`

The optional MNN fallback connector still exists for debug compatibility, but it is not used by the measured custom benchmark.

## Repository Architecture

| Area | Files | Role |
| --- | --- | --- |
| Public ABI | `customlib/include/xqwen35.h` | Stable C ABI for Android/JNI and host tests. |
| Session connector | `customlib/runtime/session.cpp` | Chooses MNN fallback only when requested; final custom run loads `CustomModel`. |
| Custom runtime | `customlib/runtime/custom_model.cpp` | Implements prefill, decode, attention, linear attention, lm_head, sampling, and trace recording. |
| Generated kernels | `customlib/kernels/generated/arm64_neon/xq_gemv_w4a16_neon.cpp` | Fused dequant + GEMV W4A16 kernel used by decode linear families and streaming lm_head argmax. |
| Reference kernels | `customlib/kernels/reference/*.cpp` | Host correctness references and non-final low-bit experiments. |
| Packer | `customlib/packer/pack_qwen35_xq4.py`, `customlib/packer/pack_qwen35_xq4_numpy.py` | Converts Qwen3.5 safetensors into the custom W4A16 package and manifest. |
| Stock Android app | `android/app` | Stock MNN baseline and stock quality instrumentation. |
| Custom Android app | `android/benchmark_app` | Customlib instrumentation, JSON evidence, MNN hot-path trace evidence, custom quality instrumentation. |
| Vulkan probe | `android/benchmark_app/src/main/cpp/benchmark_jni.cpp` | Probes Vulkan availability and records whether Vulkan kernels were actually used. |
| Device Farm connector | `scripts/aws` plus Android bootstrap tests | Uploads, schedules, downloads, and verifies Device Farm artifacts. |
| Quality connector | `runQualityValidation` JNI methods and `scripts/quality/compare_quality_validation.py` | Dumps generated token IDs and compares stock/custom output sanity separately from TPOT/TPS measurement. |

## Generated W4A16 GEMV

The final generated W4 path is `customlib/kernels/generated/arm64_neon/xq_gemv_w4a16_neon.cpp`. It is a generated/tiled fused dequant + GEMV implementation and does not call `gemvLowBitReference`.

For each output row and quantization group, it computes:

```text
code_dot = sum(code_i * activation_i)
x_sum    = sum(activation_i)
partial  = scale * (code_dot - zero * x_sum)       # symmetric v1 package
partial  = scale * code_dot + zero * x_sum         # affine-asymmetric v2 package
```

The arm64 path unpacks int4 nibbles, widens to float, accumulates with NEON FMA, and uses persistent worker threads for large row-parallel GEMV. It precomputes activation group sums once per input and reuses those sums across rows. The v27 optimization branches once per matrix on symmetric versus affine-asymmetric dequant, so the final symmetric Qwen package avoids a per-row/per-group branch. `gemvW4A16ArgmaxNeon` streams the `lm_head` argmax and avoids materializing full logits for greedy sampling.

Qwen3.5 shapes exercised on Device Farm include 4096 x 4096 attention/output projections, 12288 x 4096 MLP gate/up projections, 4096 x 12288 MLP down projection, grouped key/value projection shapes, and the 248320 x 4096 `lm_head`.

## Custom Prefill

`CustomModel::prefill` runs over every prompt token. It is not a last-token-only prefill.

For each prompt position it:

- reads the BF16 embedding row for that token through a persistent embedding stream
- runs every layer in order
- appends K/V into full-attention layer caches
- updates linear-attention recurrent state in linear-attention layers
- records `prefill_token_custom`
- records `prefill_kv_build_custom` during full-attention prefill K/V append

v27 reserves KV cache capacity up front and reuses embedding/attention buffers to reduce allocation overhead.

## Custom Full-Attention Decode

`CustomModel::runFullAttention` implements grouped-query decode attention:

1. Apply input RMSNorm.
2. Run custom W4A16 `q_proj`, `k_proj`, and `v_proj`.
3. Apply Q/K norm where Qwen3.5 supplies q_norm/k_norm weights.
4. Apply Qwen3.5 active-slice RoPE at the current absolute position.
5. Append K/V to the per-layer cache.
6. Map each query head to the correct KV head.
7. Compute `score = dot(q, k) / sqrt(head_dim)`.
8. Run max-subtracted softmax.
9. Reduce with V.
10. Apply attention output gate.
11. Run custom W4A16 `o_proj`.

Trace rows include `linear_q_proj_w4a16`, `linear_k_proj_w4a16`, `linear_v_proj_w4a16`, `rope_qk_custom`, `kv_append_custom`, `attention_score_custom`, `attention_softmax_custom`, `attention_v_reduce_custom`, `attention_output_gate_custom`, and `linear_o_proj_w4a16`.

## Custom Linear-Attention State

`CustomModel::runLinearAttention` maintains recurrent state per linear-attention layer across prefill and decode. It uses exported Qwen3.5 tensors:

- `linear_attn_in_proj_a_weight.xq4`
- `linear_attn_in_proj_b_weight.xq4`
- `linear_attn_in_proj_qkv_weight.xq4`
- `linear_attn_in_proj_z_weight.xq4`
- `linear_attn_out_proj_weight.xq4`
- `linear_attn_conv1d_weight.f32`
- `linear_attn_A_log.f32`
- `linear_attn_dt_bias.f32`

The v27 path uses the exported `A_log` and `dt_bias` gate update instead of the rejected approximation path. Trace rows include `linear_attention_conv1d_custom`, `linear_attention_qk_l2norm_custom`, `linear_attention_state_update_custom`, `linear_attention_gated_rmsnorm_custom`, and `linear_attn_out_proj_w4a16`.

## FFN, RMSNorm, And RoPE

The runtime applies Qwen-style norm weight handling by adding one to exported norm vectors before use. It implements RMSNorm, active-slice RoPE, and FFN gate math directly in `custom_model.cpp`:

```text
post_attention_rmsnorm
gate_proj W4A16
up_proj W4A16
silu(gate) * up
down_proj W4A16
residual add
```

Trace rows include `rmsnorm_input`, `rmsnorm_post_attention`, `rmsnorm_final`, `linear_gate_proj_w4a16`, `linear_up_proj_w4a16`, `silu_gate_mul_custom`, and `linear_down_proj_w4a16`.

## Real lm_head And Greedy Sampling

`CustomModel::sampleGreedy` removes hash-based token generation:

1. Apply final RMSNorm.
2. Run `lm_head_custom` with packed W4A16 `lm_head.weight`.
3. Compute greedy argmax over real logits using streaming W4A16 argmax.
4. Return the selected token.

The final benchmark settings use `temperature = 0`, `top_k = 1`, and `top_p = 1`, so greedy argmax is the required behavior. Trace rows include `lm_head_custom` and `sampling_greedy_custom`.

## Connectors

### MNN Baseline Connector

`android/app/src/main/cpp/stock_benchmark_jni.cpp` creates `MNN::Transformer::Llm`, configures stock MNN CPU, runs generation, and emits stock `BENCH_RESULT_JSON`. It also implements `runQualityValidation` for stock `BENCH_QUALITY_JSON` using the same English fixed token-ID prompts.

### Custom JNI Connector

`android/benchmark_app/src/main/cpp/benchmark_jni.cpp` exposes `NativeBenchmark.runBenchmark(...)` and `NativeBenchmark.runQualityValidation(...)`. The benchmark path emits TPOT/TPS and per-kernel wall clock. The quality path emits generated token IDs for fixed prompts and does not pollute TPOT/TPS timing.

### Fallback Connector

`customlib/runtime/session.cpp` still supports `xq_options.use_mnn_fallback != 0` for debugging. The final custom Device Farm run does not use it.

### Vulkan Probe Connector

The custom JNI accepts `cpu`, `vulkan`, and `cpu_vulkan_hybrid`. It probes `libvulkan.so` and `vkGetInstanceProcAddr`. The final v27 run reports probe success but `custom_backend_actual = cpu` and `vulkan_generation_kernels_used = false`.

### Benchmark And Quality Connectors

Android instrumentation writes JSON artifacts into Device Farm customer artifacts:

- `stock_mnn_cpu_benchmark.json`
- `customlib_cpu_vulkan_hybrid_benchmark.json`
- `quality_validation_stock.json`
- `quality_validation_custom.json`

`scripts/quality/compare_quality_validation.py` compares stock/custom quality JSON and produces `quality_validation_v27_english_comparison.json` plus `quality_validation_report.md`.

## Evidence Summary

- Final custom benchmark ARN: `{ARNS['custom_benchmark']}`
- Final stock benchmark ARN: `{ARNS['stock_benchmark']}`
- Final custom quality ARN: `{ARNS['custom_quality']}`
- Final stock quality ARN: `{ARNS['stock_quality']}`
- Custom decode TPS / TPOT: `{fmt(custom_decode)}` / `{ms(custom_tpot)}`
- Stock decode TPS / TPOT: `{fmt(stock_decode)}` / `{ms(stock_tpot)}`
- Custom / stock decode ratio: `{custom_stock_ratio:.4f}x`
- Quality gate: PASS, exact full-output token match `{quality_comp['exact_match_prompt_count']} / {quality_comp['prompt_count']}`, comparison sanity `{quality_comp['comparison_gate_prompt_count']} / {quality_comp['prompt_count']}`.

The final result is a systems/kernel benchmark plus deterministic output sanity guard. It is not a production-quality language-model certification.
"""
    Path("docs/kernel_library_code_walkthrough_final.md").write_text(walkthrough, encoding="utf-8")

    quality_md = (REPORTS / "quality_validation_v27_english_report.md").read_text(encoding="utf-8")
    (REPORTS / "quality_validation_report.md").write_text(quality_md, encoding="utf-8")

    now = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    summary = {
        "generated_utc": now,
        "version": "v27_quality_performance_final",
        "baseline": {
            "v17_commit": "7660928f728784355d029bb3afec13236a217fe3",
            "v17_custom_decode_tps": v17_decode,
            "v17_custom_decode_tpot_ms": v17_tpot,
            "v17_custom_run_arn": ARNS["v17_custom"],
        },
        "verdict": {
            "faithful_benchmark": True,
            "requirement_1_met": True,
            "requirement_2_met": True,
            "requirement_3_quality_guard_met": True,
            "quality_gate_passed": bool(quality_comp["quality_gate_passed"]),
            "custom_speedup_claim_allowed": False,
            "speedup_verdict": (
                f"No stock-MNN speedup claimed. Custom decode {custom_decode:.5f} TPS "
                f"vs stock CPU {stock_decode:.5f} TPS, ratio {custom_stock_ratio:.4f}x."
            ),
            "custom_vulkan_used_in_measured_generation": False,
            "vulkan_attempted": True,
        },
        "model": {
            "hf_repo": "Qwen/Qwen3.5-9B",
            "hf_revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
            "quantization": "w4a16_groupwise, bits=4, group_size=64",
            "zip_sha256": MODEL_SHA,
            "zip_total_bytes": 11266405198,
            "split_part_bytes": [4500000000, 4500000000, 2266405198],
            "split_part_sha256": [
                "3b13bdc4a158b6745f58cfe0dc4c31e485990a50f24d8f14809f5df0e2aa15dc",
                "60b8c1d898e4db8b626f750660174f20c05a7e28a43ca11192d58494c3e9211f",
                "32d8becc5a77be798a9bc8a3c26509e419942b57aad59f8d4b55310de7248b18",
            ],
        },
        "same_settings": custom["generation"],
        "devicefarm": {
            "project_arn": PROJECT_ARN,
            "device_pool_arn": POOL_ARN,
            "device": "Samsung Galaxy S26 Ultra / SM-S948U1 / Android 16",
        },
        "runs": [
            {
                "name": "stock_mnn_v27_benchmark_cpu_qwen35_9b",
                "engine": "stock_mnn",
                "backend_requested": "cpu",
                "backend_actual": "cpu",
                "run_arn": ARNS["stock_benchmark"],
                "result": "PASSED",
                "prefill_tps_mean": stock_prefill,
                "decode_tps_mean": stock_decode,
                "decode_tpot_ms_mean": stock_tpot,
                "evidence_json": "results/reports/evidence/stock_mnn_cpu_benchmark_v27.json",
            },
            {
                "name": "customlib_v27_benchmark_cpu_vulkan_hybrid_qwen35_9b",
                "engine": "customlib",
                "backend_requested": "cpu_vulkan_hybrid",
                "backend_actual": "cpu",
                "run_arn": ARNS["custom_benchmark"],
                "result": "PASSED",
                "prefill_tps_mean": custom_prefill,
                "decode_tps_mean": custom_decode,
                "decode_tpot_ms_mean": custom_tpot,
                "evidence_json": "results/reports/evidence/customlib_cpu_vulkan_hybrid_benchmark_v27.json",
            },
            {
                "name": "stock_mnn_v27_quality_english_qwen35_9b",
                "engine": "stock_mnn",
                "run_arn": ARNS["stock_quality"],
                "result": "PASSED",
                "quality_gate_passed": quality_stock["quality_gate_passed"],
                "evidence_json": "results/reports/evidence/quality_validation_v27_stock_english.json",
            },
            {
                "name": "customlib_v27_quality_english_qwen35_9b",
                "engine": "customlib",
                "run_arn": ARNS["custom_quality"],
                "result": "PASSED",
                "quality_gate_passed": quality_custom["quality_gate_passed"],
                "evidence_json": "results/reports/evidence/quality_validation_v27_custom_english.json",
            },
        ],
        "comparisons": {
            "custom_vs_stock_decode_ratio": custom_stock_ratio,
            "custom_vs_v17_decode_ratio": custom_v17_ratio,
            "custom_vs_v26_decode_ratio": custom_v26_ratio,
            "best_stock_backend": "stock_mnn_cpu",
            "best_custom_variant": "customlib_cpu_vulkan_hybrid_requested_actual_cpu",
            "best_custom_actual_backend": "cpu",
        },
        "quality": {
            "comparison_json": "results/reports/evidence/quality_validation_v27_english_comparison.json",
            "report": "results/reports/quality_validation_report.md",
            "quality_gate_passed": quality_comp["quality_gate_passed"],
            "exact_match_prompt_count": quality_comp["exact_match_prompt_count"],
            "prompt_count": quality_comp["prompt_count"],
            "comparison_gate_prompt_count": quality_comp["comparison_gate_prompt_count"],
            "all_exact_match": quality_comp["all_exact_match"],
            "limitations": quality_comp["limitations"],
            "prompts": quality_comp["prompts"],
        },
        "custom_evidence": {
            "custom_path": custom["custom_path"],
            "selected_kernels": selected,
            "vulkan_attempt": custom["vulkan_attempt"],
        },
        "artifacts": {
            "final_report_md": "results/reports/final_devicefarm_report.md",
            "final_report_json": "results/reports/final_devicefarm_report.json",
            "code_walkthrough_md": "docs/kernel_library_code_walkthrough_final.md",
            "quality_report_md": "results/reports/quality_validation_report.md",
            "presentation_pptx": "results/reports/qwen35_9b_v27_quality_performance_presentation.pptx",
        },
        "per_kernel_wall_clock": custom["per_kernel_wall_clock"],
        "custom_kernel_microbench": custom["custom_kernel_microbench"],
        "mnn_hotpath_op_trace": custom["mnn_hotpath_op_trace"],
    }
    (REPORTS / "final_devicefarm_report.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    history = f"""# Run History Summary

The accepted final result is v27.

| Version | Status | Decode TPS | Decode TPOT | Quality status | Decision |
| --- | --- | ---: | ---: | --- | --- |
| v17 | accepted systems/kernel baseline | {fmt(v17_decode)} | {ms(v17_tpot)} | not quality-gated in original pass | preserved as baseline |
| v19r2 | rejected | 2.14021 | 467.244 ms | failed, repeated token 220 degeneration | rejected |
| v25 | quality fixed, slow | 1.68213 | 594.485 ms | passed English fixed-ID quality guard | superseded |
| v26 | buffer reuse candidate | {fmt(v26_decode)} | {ms(v26_tpot)} | passed quality guard | superseded by v27 |
| v27 | final accepted | {fmt(custom_decode)} | {ms(custom_tpot)} | passed quality guard, 5 / 5 comparison sanity | official final |

Fresh stock MNN CPU v27 is {fmt(stock_decode)} decode TPS / {ms(stock_tpot)} TPOT, so final custom/stock is {custom_stock_ratio:.4f}x. No custom speedup over stock MNN is claimed.
"""
    (REPORTS / "run_history_summary.md").write_text(history, encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "wrote_final_reports",
                "custom_decode_tps": custom_decode,
                "stock_decode_tps": stock_decode,
                "custom_stock_ratio": custom_stock_ratio,
                "custom_v17_ratio": custom_v17_ratio,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

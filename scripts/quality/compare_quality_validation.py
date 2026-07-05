#!/usr/bin/env python3
"""Compare stock MNN and customlib quality-validation token dumps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def levenshtein(a: list[int], b: list[int]) -> int:
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, token_a in enumerate(a, start=1):
        current = [i]
        for j, token_b in enumerate(b, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (0 if token_a == token_b else 1)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]


def prefix_match_len(a: list[int], b: list[int]) -> int:
    count = 0
    for token_a, token_b in zip(a, b):
        if token_a != token_b:
            break
        count += 1
    return count


def token_match_rate(a: list[int], b: list[int]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    width = max(len(a), len(b))
    matches = sum(1 for token_a, token_b in zip(a, b) if token_a == token_b)
    return matches / width


def prompts_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in payload.get("prompts", [])}


def basic_prompt_ok(prompt: dict[str, Any]) -> bool:
    return (
        prompt.get("invalid_token_count", 1) == 0
        and not prompt.get("empty_output", True)
        and not prompt.get("obvious_degenerate_output", True)
    )


def first_mismatch(a: list[int], b: list[int]) -> int | None:
    for index, (token_a, token_b) in enumerate(zip(a, b)):
        if token_a != token_b:
            return index
    if len(a) != len(b):
        return min(len(a), len(b))
    return None


def compare(stock: dict[str, Any], custom: dict[str, Any], min_overlap: float, min_prefix: int) -> dict[str, Any]:
    stock_prompts = prompts_by_id(stock)
    custom_prompts = prompts_by_id(custom)
    prompt_ids = sorted(set(stock_prompts) | set(custom_prompts))
    rows: list[dict[str, Any]] = []
    exact_count = 0
    comparison_gate_count = 0
    for prompt_id in prompt_ids:
        stock_prompt = stock_prompts.get(prompt_id)
        custom_prompt = custom_prompts.get(prompt_id)
        if stock_prompt is None or custom_prompt is None:
            rows.append(
                {
                    "id": prompt_id,
                    "status": "missing_prompt",
                    "exact_match": False,
                    "comparison_gate_passed": False,
                }
            )
            continue
        stock_tokens = [int(x) for x in stock_prompt.get("generated_token_ids", [])]
        custom_tokens = [int(x) for x in custom_prompt.get("generated_token_ids", [])]
        exact = stock_tokens == custom_tokens
        prefix = prefix_match_len(stock_tokens, custom_tokens)
        rate = token_match_rate(stock_tokens, custom_tokens)
        edit = levenshtein(stock_tokens, custom_tokens)
        norm_edit = edit / max(1, max(len(stock_tokens), len(custom_tokens)))
        stock_ok = basic_prompt_ok(stock_prompt)
        custom_ok = basic_prompt_ok(custom_prompt)
        mismatch_index = first_mismatch(stock_tokens, custom_tokens)
        comparison_gate = exact or (
            stock_ok
            and custom_ok
            and (rate >= min_overlap or prefix >= min_prefix)
        )
        if exact:
            exact_count += 1
        if comparison_gate:
            comparison_gate_count += 1
        rows.append(
            {
                "id": prompt_id,
                "prompt_kind": custom_prompt.get("prompt_kind") or stock_prompt.get("prompt_kind"),
                "status": "ok",
                "stock_basic_ok": stock_ok,
                "custom_basic_ok": custom_ok,
                "exact_match": exact,
                "prefix_match_length": prefix,
                "token_match_rate": rate,
                "edit_distance": edit,
                "normalized_edit_distance": norm_edit,
                "first_mismatch_position": mismatch_index,
                "comparison_gate_passed": comparison_gate,
                "stock_generated_token_count": len(stock_tokens),
                "custom_generated_token_count": len(custom_tokens),
                "stock_generated_token_ids": stock_tokens,
                "custom_generated_token_ids": custom_tokens,
                "stock_decoded_text_available": bool(stock_prompt.get("decoded_text_available")),
                "custom_decoded_text_available": bool(custom_prompt.get("decoded_text_available")),
                "stock_decoded_generated_text": stock_prompt.get("decoded_generated_text", ""),
                "custom_decoded_generated_text": custom_prompt.get("decoded_generated_text", ""),
            }
        )
    all_present = all(row.get("status") == "ok" for row in rows)
    stock_native_ok = stock.get("quality_gate_passed") is True
    custom_native_ok = custom.get("quality_gate_passed") is True
    all_basic_ok = all(row.get("stock_basic_ok") and row.get("custom_basic_ok") for row in rows if row.get("status") == "ok")
    all_comparison_ok = all(row.get("comparison_gate_passed") for row in rows)
    quality_gate_passed = bool(stock_native_ok and custom_native_ok and all_present and all_basic_ok and all_comparison_ok)
    return {
        "schema_version": 1,
        "artifact_type": "quality_validation_comparison",
        "status": "ok" if quality_gate_passed else "rejected",
        "quality_gate_passed": quality_gate_passed,
        "stock_native_quality_gate_passed": stock_native_ok,
        "custom_native_quality_gate_passed": custom_native_ok,
        "exact_match_prompt_count": exact_count,
        "prompt_count": len(prompt_ids),
        "all_exact_match": exact_count == len(prompt_ids) and len(prompt_ids) > 0,
        "comparison_gate_prompt_count": comparison_gate_count,
        "comparison_acceptance_rule": {
            "exact_match_passes": True,
            "mismatch_passes_when_basic_sanity_and_overlap": True,
            "min_token_match_rate": min_overlap,
            "min_prefix_match_length": min_prefix,
        },
        "limitations": [
            "Validation uses fixed token-ID prompts so both engines receive identical prompt IDs.",
            "Decoded custom text is not claimed unless tokenizer decode is available in the custom artifact.",
            "This is a deterministic sanity guard, not a production semantic-quality benchmark.",
        ],
        "prompts": rows,
    }


def write_report(comparison: dict[str, Any], stock_path: Path, custom_path: Path, out_path: Path, stock_run_arn: str, custom_run_arn: str) -> None:
    lines: list[str] = []
    lines.append("# Output Correctness / Quality Guard")
    lines.append("")
    lines.append("TPS/TPOT measure speed, not semantic quality. This validation compares deterministic generated-token dumps from stock MNN and customlib on the same fixed token-ID prompt suite.")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"- Quality gate passed: {'YES' if comparison['quality_gate_passed'] else 'NO'}")
    lines.append(f"- Exact token match for all prompts: {'YES' if comparison['all_exact_match'] else 'NO'}")
    lines.append(f"- Exact-match prompts: {comparison['exact_match_prompt_count']} / {comparison['prompt_count']}")
    lines.append(f"- Comparison-gate prompts: {comparison['comparison_gate_prompt_count']} / {comparison['prompt_count']}")
    if stock_run_arn:
        lines.append(f"- Stock validation run ARN: `{stock_run_arn}`")
    if custom_run_arn:
        lines.append(f"- Custom validation run ARN: `{custom_run_arn}`")
    lines.append(f"- Stock evidence JSON: `{stock_path.as_posix()}`")
    lines.append(f"- Custom evidence JSON: `{custom_path.as_posix()}`")
    lines.append("")
    lines.append("## Prompt Comparison")
    lines.append("")
    lines.append("| Prompt | Exact | Prefix | Token match | Edit distance | First mismatch | Custom sanity |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in comparison["prompts"]:
        if row.get("status") != "ok":
            lines.append(f"| {row['id']} | no | 0 | 0.000 | n/a | n/a | no |")
            continue
        first_mismatch_value = row["first_mismatch_position"]
        first_mismatch = "none" if first_mismatch_value is None else str(first_mismatch_value)
        lines.append(
            "| {id} | {exact} | {prefix} | {rate:.3f} | {edit} | {mismatch} | {sanity} |".format(
                id=row["id"],
                exact="yes" if row["exact_match"] else "no",
                prefix=row["prefix_match_length"],
                rate=row["token_match_rate"],
                edit=row["edit_distance"],
                mismatch=first_mismatch,
                sanity="yes" if row.get("custom_basic_ok") else "no",
            )
        )
    lines.append("")
    lines.append("## Token Examples")
    lines.append("")
    for row in comparison["prompts"]:
        if row.get("status") != "ok":
            continue
        lines.append(f"### {row['id']}")
        lines.append("")
        lines.append(f"- Stock tokens: `{row['stock_generated_token_ids'][:32]}`")
        lines.append(f"- Custom tokens: `{row['custom_generated_token_ids'][:32]}`")
        if row.get("stock_decoded_text_available"):
            text = str(row.get("stock_decoded_generated_text", "")).replace("\n", "\\n")
            lines.append(f"- Stock decoded text: `{text[:500]}`")
        if row.get("custom_decoded_text_available"):
            text = str(row.get("custom_decoded_generated_text", "")).replace("\n", "\\n")
            lines.append(f"- Custom decoded text: `{text[:500]}`")
        lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("The custom library is validated here for operator correctness, deterministic decode-path execution, and basic generated-token sanity against stock MNN. It is not claimed as a production-quality model replacement; full semantic quality validation with perplexity and downstream task benchmarks remains future work.")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", type=Path, required=True)
    parser.add_argument("--custom", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--stock-run-arn", default="")
    parser.add_argument("--custom-run-arn", default="")
    parser.add_argument("--min-overlap", type=float, default=0.20)
    parser.add_argument("--min-prefix", type=int, default=4)
    args = parser.parse_args()

    stock = load_json(args.stock)
    custom = load_json(args.custom)
    comparison = compare(stock, custom, args.min_overlap, args.min_prefix)
    comparison["devicefarm"] = {
        "stock_validation_run_arn": args.stock_run_arn,
        "custom_validation_run_arn": args.custom_run_arn,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(comparison, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(comparison, args.stock, args.custom, args.out_md, args.stock_run_arn, args.custom_run_arn)
    if not comparison["quality_gate_passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

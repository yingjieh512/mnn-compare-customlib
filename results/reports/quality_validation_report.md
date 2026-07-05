# Output Correctness / Quality Guard

TPS/TPOT measure speed, not semantic quality. This validation compares deterministic generated-token dumps from stock MNN and customlib on the same fixed token-ID prompt suite.

## Verdict

- Quality gate passed: NO
- Exact token match for all prompts: NO
- Exact-match prompts: 0 / 5
- Comparison-gate prompts: 0 / 5
- Stock validation run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/28a7b8ce-cb81-4e31-8498-c59164e9cdaa`
- Custom validation run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/e8582532-a655-4619-b348-9c07b5740f3d`
- Stock evidence JSON: `results/reports/evidence/quality_validation_v19r2_stock.json`
- Custom evidence JSON: `results/reports/evidence/quality_validation_v19r2_custom.json`

## Prompt Comparison

| Prompt | Exact | Prefix | Token match | Edit distance | First mismatch | Custom sanity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| chinese_short | no | 1 | 0.094 | 29 | 1 | no |
| code_like | no | 0 | 0.031 | 31 | 0 | no |
| english_factual | no | 0 | 0.000 | 32 | 0 | no |
| long_512_token_style | no | 0 | 0.031 | 31 | 0 | no |
| math_reasoning | no | 0 | 0.000 | 32 | 0 | yes |

## Token Examples

### chinese_short

- Stock tokens: `[220, 17, 15, 16, 22, 198, 17, 198, 104321, 3837, 34187, 222, 220, 17, 15, 16, 23, 198, 18, 198, 104321, 3837, 34187, 222, 220, 17, 15, 16, 24, 198, 19, 198]`
- Custom tokens: `[220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: ` 2017\n2\n导师asure ♀ 2018\n3\n导师asure ♀ 2019\n4\n`

### code_like

- Stock tokens: `[472, 401, 9338, 11, 293, 220, 16, 19, 15, 15, 8, 198, 17, 198, 365, 290, 318, 77, 13, 295, 13, 401, 1147, 91897, 771, 7972, 8, 198, 18, 198, 365, 290]`
- Custom tokens: `[220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `ine de France, d 1400)\n2\nabed (n. m. de la langue arabe)\n3\nabed`

### english_factual

- Stock tokens: `[198, 760, 5597, 315, 9625, 369, 264, 491, 2993, 314, 198, 395, 470, 11, 28191, 11, 321, 3999, 4534, 23895, 198, 18384, 8111, 3545, 13, 1049, 369, 5995, 310, 381, 198, 2506]`
- Custom tokens: `[220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `\nThe Portom Ze is a new kind of\nportable, lightweight, and easy-to-use\nelectronic device. It is designed to be\nused`

### long_512_token_style

- Stock tokens: `[16, 198, 220, 271, 25, 30, 271, 25, 30, 271, 25, 4458, 11, 17, 18, 19, 20, 21, 22, 23, 24, 16, 271, 25, 4458, 11, 17, 18, 19, 20, 21, 22]`
- Custom tokens: `[220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `1\n \n\n:?\n\n:?\n\n:?.,234567891\n\n:?.,234567`

### math_reasoning

- Stock tokens: `[18, 271, 332, 17, 332, 198, 16, 15, 10, 17, 28, 16, 17, 198, 18, 10, 20, 28, 23, 198, 16, 20, 10, 30, 283, 17, 15, 198, 332, 16, 15, 332]`
- Custom tokens: `[16, 198, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `3\n\n**2**\n10+2=12\n3+5=8\n15+? =20\n**10**`

## Limitations

The custom library is validated here for operator correctness, deterministic decode-path execution, and basic generated-token sanity against stock MNN. It is not claimed as a production-quality model replacement; full semantic quality validation with perplexity and downstream task benchmarks remains future work.

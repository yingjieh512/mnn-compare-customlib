# Output Correctness / Quality Guard

TPS/TPOT measure speed, not semantic quality. This validation compares deterministic generated-token dumps from stock MNN and customlib on the same fixed token-ID prompt suite.

## Verdict

- Quality gate passed: NO
- Exact token match for all prompts: NO
- Exact-match prompts: 0 / 5
- Comparison-gate prompts: 3 / 5
- Stock validation run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/e3c2513e-c116-4eaf-a9f6-cfb7ebae0262`
- Custom validation run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/baac7bb4-30d8-477e-bbfc-9d9ea4a7afc7`
- Stock evidence JSON: `results/reports/evidence/quality_validation_v22_stock_greedy.json`
- Custom evidence JSON: `results/reports/evidence/quality_validation_v22_custom_norm_greedy.json`

## Prompt Comparison

| Prompt | Exact | Prefix | Token match | Edit distance | First mismatch | Custom sanity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| chinese_short | no | 1 | 0.188 | 22 | 1 | yes |
| code_like | no | 0 | 0.000 | 32 | 0 | yes |
| english_factual | no | 7 | 0.250 | 24 | 7 | yes |
| long_512_token_style | no | 20 | 0.625 | 3 | 20 | yes |
| math_reasoning | no | 5 | 0.375 | 19 | 5 | yes |

## Token Examples

### chinese_short

- Stock tokens: `[198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321]`
- Custom tokens: `[198, 17, 198, 104321, 3837, 34187, 222, 111308, 1773, 198, 18, 198, 104321, 3837, 34187, 222, 111308, 1773, 198, 19, 198, 104321, 3837, 34187, 222, 111308, 1773, 198, 20, 198, 104321, 3837]`
- Stock decoded text: `\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师`

### code_like

- Stock tokens: `[13, 220, 16, 15, 15, 15, 13, 198, 760, 2614, 369, 264, 2880, 314, 279, 668, 314, 279, 3200, 4248, 13, 3629, 3554, 598, 11, 314, 279, 49475, 314, 769, 13, 81906]`
- Custom tokens: `[11, 293, 2285, 8, 198, 16, 198, 16, 198, 16, 198, 16, 198, 16, 198, 16, 198, 16, 198, 16, 198, 16, 198, 16, 198, 16, 198, 16, 198, 16, 198, 16]`
- Stock decoded text: `. 1000.\nThe following is a copy of the will of the late Mr. John Abell, of the parish of St. Giles`

### english_factual

- Stock tokens: `[198, 760, 5597, 315, 9625, 369, 264, 491, 2993, 314, 198, 395, 421, 369, 1602, 5617, 303, 279, 198, 6864, 315, 9625, 13, 1049, 369, 264, 2548, 421, 369, 198, 44697, 383]`
- Custom tokens: `[198, 760, 5597, 315, 9625, 369, 264, 2526, 11, 198, 258, 36312, 11, 198, 6082, 26922, 198, 23152, 198, 9497, 9790, 310, 279, 198, 22885, 8503, 321, 198, 71621, 314, 279, 198]`
- Stock decoded text: `\nThe Portom Ze is a new kind of\nport that is being built in the\nPortom Ze. It is a port that is\nbuilt on`

### long_512_token_style

- Stock tokens: `[16, 198, 220, 271, 25, 30, 2487, 17, 18, 19, 20, 21, 22, 23, 24, 16, 198, 220, 271, 25, 4458, 11, 17, 18, 19, 20, 21, 22, 23, 24, 16, 198]`
- Custom tokens: `[16, 198, 220, 271, 25, 30, 2487, 17, 18, 19, 20, 21, 22, 23, 24, 16, 198, 220, 271, 25, 12259, 17, 18, 19, 20, 21, 22, 23, 24, 16, 198, 220]`
- Stock decoded text: `1\n \n\n:?.,234567891\n \n\n:?.,234567891\n`

### math_reasoning

- Stock tokens: `[17, 10, 17, 28, 19, 198, 18, 10, 18, 28, 21, 198, 19, 10, 19, 28, 23, 198, 20, 10, 20, 28, 16, 15, 198, 21, 10, 21, 28, 16, 17, 198]`
- Custom tokens: `[17, 10, 17, 28, 19, 220, 17, 10, 17, 28, 19, 220, 17, 10, 17, 28, 19, 220, 17, 10, 17, 28, 19, 220, 17, 10, 17, 28, 19, 220, 17, 10]`
- Stock decoded text: `2+2=4\n3+3=6\n4+4=8\n5+5=10\n6+6=12\n`

## Limitations

The custom library is validated here for operator correctness, deterministic decode-path execution, and basic generated-token sanity against stock MNN. It is not claimed as a production-quality model replacement; full semantic quality validation with perplexity and downstream task benchmarks remains future work.

# Output Correctness / Quality Guard

TPS/TPOT measure speed, not semantic quality. This validation compares deterministic generated-token dumps from stock MNN and customlib on the same fixed token-ID prompt suite.

## Verdict

- Quality gate passed: NO
- Exact token match for all prompts: NO
- Exact-match prompts: 0 / 5
- Comparison-gate prompts: 1 / 5
- Stock validation run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/83043bec-da9c-45fd-867c-29fc60aa4bf5`
- Custom validation run ARN: `arn:aws:devicefarm:us-west-2:884244642857:run:64d2cc31-abd6-49f8-97da-162f82410bc0/519413e3-cda8-4489-add7-3f14d1b0a694`
- Stock evidence JSON: `results/reports/evidence/quality_validation_v21_stock_reference.json`
- Custom evidence JSON: `results/reports/evidence/quality_validation_v21_current_custom.json`

## Prompt Comparison

| Prompt | Exact | Prefix | Token match | Edit distance | First mismatch | Custom sanity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| chinese_short | no | 0 | 0.062 | 30 | 0 | yes |
| code_like | no | 0 | 0.219 | 25 | 0 | yes |
| english_factual | no | 1 | 0.031 | 31 | 1 | yes |
| long_512_token_style | no | 0 | 0.156 | 27 | 0 | no |
| math_reasoning | no | 1 | 0.156 | 27 | 1 | yes |

## Token Examples

### chinese_short

- Stock tokens: `[198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321, 198, 104321]`
- Custom tokens: `[220, 16, 198, 16, 198, 198, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师\n导师`

### code_like

- Stock tokens: `[13, 220, 16, 22, 11, 220, 17, 19, 11, 220, 17, 24, 11, 220, 18, 15, 11, 220, 18, 17, 11, 220, 18, 19, 11, 220, 18, 21, 11, 220, 19, 16]`
- Custom tokens: `[198, 198, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `. 17, 24, 29, 30, 32, 34, 36, 41`

### english_factual

- Stock tokens: `[198, 760, 5597, 315, 9625, 369, 279, 803, 2574, 310, 279, 198, 6864, 315, 9625, 303, 279, 2236, 13, 561, 5597, 315, 9625, 369, 198, 1719, 803, 314, 279, 5597, 315, 9625]`
- Custom tokens: `[198, 198, 198, 198, 220, 198, 220, 198, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `\nThe Portom Ze is the name given to the\nPortom Ze in the book. The Portom Ze is\nthe name of the Portom Ze`

### long_512_token_style

- Stock tokens: `[16, 198, 220, 271, 25, 30, 2487, 17, 18, 19, 20, 21, 22, 23, 24, 16, 198, 220, 271, 25, 4458, 198, 220, 271, 25, 4458, 198, 220, 271, 25, 4458, 198]`
- Custom tokens: `[198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198]`
- Stock decoded text: `1\n \n\n:?.,234567891\n \n\n:?.\n \n\n:?.\n \n\n:?.\n`

### math_reasoning

- Stock tokens: `[16, 10, 16, 19279, 198, 17, 10, 17, 28, 19, 220, 16, 10, 16, 28, 17, 198, 3710, 369, 220, 18, 10, 18, 30, 198, 3710, 369, 220, 19, 10, 19, 30]`
- Custom tokens: `[16, 198, 16, 16, 198, 16, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198, 198]`
- Stock decoded text: `1+1=?\n2+2=4 1+1=2\nWhat is 3+3?\nWhat is 4+4?`

## Limitations

The custom library is validated here for operator correctness, deterministic decode-path execution, and basic generated-token sanity against stock MNN. It is not claimed as a production-quality model replacement; full semantic quality validation with perplexity and downstream task benchmarks remains future work.

# Output Correctness / Quality Guard

TPS/TPOT measure speed, not semantic quality. This validation compares deterministic generated-token dumps from stock MNN and customlib on the same fixed token-ID prompt suite.

## Verdict

- Quality gate passed: NO
- Exact token match for all prompts: NO
- Exact-match prompts: 0 / 5
- Comparison-gate prompts: 0 / 5
- Stock evidence JSON: `results/reports/evidence/quality_validation_v20r2_current_stock.json`
- Custom evidence JSON: `results/reports/evidence/quality_validation_v20r2_current_custom.json`

## Prompt Comparison

| Prompt | Exact | Prefix | Token match | Edit distance | First mismatch | Custom sanity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| chinese_short | no | 0 | 0.000 | 32 | 0 | no |
| code_like | no | 0 | 0.000 | 32 | 0 | no |
| english_factual | no | 0 | 0.031 | 31 | 0 | no |
| long_512_token_style | no | 0 | 0.094 | 29 | 0 | no |
| math_reasoning | no | 0 | 0.062 | 30 | 0 | yes |

## Token Examples

### chinese_short

- Stock tokens: `[198, 17, 198, 104321, 18523, 34187, 222, 111308, 1773, 198, 18, 198, 104321, 18523, 34187, 222, 97205, 1773, 198, 19, 198, 104321, 18523, 2765, 17980, 97205, 1773, 198, 20, 198, 104321, 18523]`
- Custom tokens: `[220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `\n2\n导师sure ♀不幸search\n3\n导师sure ♀幸search\n4\n导师sure ♂幸search\n5\n导师sure`

### code_like

- Stock tokens: `[472, 11, 1778, 293, 6, 15469, 455, 265, 11, 1778, 401, 1147, 44636, 401, 9338, 11, 1778, 401, 1147, 44636, 401, 89311, 11, 1778, 401, 1147, 44636, 293, 6, 2014, 192638, 13]`
- Custom tokens: `[220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `ine, et d'Angleterre, et de la maison de France, et de la maison de Bourbon, et de la maison d'Anjou.`

### english_factual

- Stock tokens: `[198, 760, 5597, 17762, 2891, 14665, 198, 1634, 198, 21595, 604, 13, 710, 13, 198, 13155, 7013, 220, 16, 24, 24, 24, 198, 21595, 604, 13, 710, 13, 198, 2324, 10199, 14721]`
- Custom tokens: `[220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `\nThe Portoroze Story\nby\nDavid J. K.\nCopyright © 1999\nDavid J. K.\nAll Rights Reserved`

### long_512_token_style

- Stock tokens: `[16, 198, 220, 271, 25, 30, 2487, 17, 18, 19, 20, 21, 22, 23, 24, 16, 198, 220, 271, 25, 12259, 17, 18, 19, 20, 21, 22, 23, 24, 16, 198, 220]`
- Custom tokens: `[220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `1\n \n\n:?.,234567891\n \n\n:?,234567891\n `

### math_reasoning

- Stock tokens: `[18, 10, 18, 28, 10992, 19, 10, 19, 19279, 271, 8160, 513, 279, 10926, 310, 678, 6673, 5154, 25, 271, 9, 256, 2972, 17, 478, 220, 17, 283, 220, 19, 332, 198]`
- Custom tokens: `[16, 198, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220, 220]`
- Stock decoded text: `3+3=？4+4=?\n\nHere are the answers to your math problems:\n\n*   **2 + 2 = 4**\n`

## Limitations

The custom library is validated here for operator correctness, deterministic decode-path execution, and basic generated-token sanity against stock MNN. It is not claimed as a production-quality model replacement; full semantic quality validation with perplexity and downstream task benchmarks remains future work.

# Run History Summary

The accepted final result is v27.

| Version | Status | Decode TPS | Decode TPOT | Quality status | Decision |
| --- | --- | ---: | ---: | --- | --- |
| v17 | accepted systems/kernel baseline | 1.93417 | 517.018 ms | not quality-gated in original pass | preserved as baseline |
| v19r2 | rejected | 2.14021 | 467.244 ms | failed, repeated token 220 degeneration | rejected |
| v25 | quality fixed, slow | 1.68213 | 594.485 ms | passed English fixed-ID quality guard | superseded |
| v26 | buffer reuse candidate | 1.75582 | 569.535 ms | passed quality guard | superseded by v27 |
| v27 | final accepted | 2.11989 | 471.723 ms | passed quality guard, 5 / 5 comparison sanity | official final |

Fresh stock MNN CPU v27 is 2.26870 decode TPS / 440.780 ms TPOT, so final custom/stock is 0.9344x. No custom speedup over stock MNN is claimed.

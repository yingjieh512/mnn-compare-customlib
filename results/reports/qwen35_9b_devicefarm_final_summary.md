# Superseded Device Farm Summary Alias

This file is retained only for compatibility with earlier generated report names.

The official final report is `results/reports/final_devicefarm_report.md`.

Current official decision:

- Official final: v17 backend sweep.
- Requirement 1 met: YES.
- Requirement 2 met: YES.
- Custom speedup claimed: NO.
- v18r2 optimization candidate: rejected after the v19r2 output-quality guard.
- Quality validation report: `results/reports/quality_validation_report.md`.
- Rejection note: `results/reports/optimization_attempt_v18.md`.

The rejected v18r2 performance candidate measured `2.14021` decode TPS, but custom quality validation failed with degenerate repeated token `220` outputs and exact token match `0 / 5`. Therefore it is not the official final result.

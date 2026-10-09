# Results

- `qwen2.5:7b` through the openai-compatible client: 30 runs, 2026-10-09 to 2026-10-09

## AEB-lite

### Table 1. Metrics by condition

| Condition | Runs | Tests | Rows rejected | Error rate | Boundary recall (simple / strict) | Input classes | Detection: seeded | Detection: mutants | LLM calls |
|---|---|---|---|---|---|---|---|---|---|
| B1 enhanced prompt | 10 | 24.3 ± 6.3 | 0.4 ± 0.7 | 43% ± 10% | 71% ± 15% / 63% ± 17% | 76% ± 14% | 73% ± 13% | 71% ± 11% | 1.0 ± 0.0 |
| FR feedback refinement | 10 | 32.7 ± 7.3 | 0.7 ± 1.3 | 21% ± 15% | 98% ± 6% / 80% ± 17% | 96% ± 7% | 80% ± 12% | 90% ± 12% | 7.2 ± 1.5 |
| FR, decision table instead of vote | 10 | 32.6 ± 6.2 | 0.6 ± 1.1 | 23% ± 14% | 100% ± 0% / 85% ± 20% | 97% ± 6% | 77% ± 10% | 87% ± 10% | 6.4 ± 0.7 |

### Table 2. Seeded defects detected (runs that detected / runs)

| Defect | Type | B0 | B1 | FR | H |
|---|---|---|---|---|---|
| F1 | boundary operator |  | 10/10 | 10/10 |  |
| F2 | boundary operator |  | 10/10 | 10/10 |  |
| F3 | boundary operator |  | 10/10 | 10/10 |  |
| F4 | missing check |  | 5/10 | 6/10 |  |
| F5 | null handling |  | 5/10 | 8/10 |  |
| F6 | check order |  | 10/10 | 9/10 |  |
| F7 | numeric conversion |  | 1/10 | 3/10 |  |

### Table 3. Statistical comparisons

| Comparison | Test | Means | A12 | p | p (Holm) |
|---|---|---|---|---|---|
| FR vs B1: error_rate | Wilcoxon | 21% vs 43% | 0.14 | 0.002 | 0.012 |
| FR vs B1: detection_seeded | Wilcoxon | 80% vs 73% | 0.68 | 0.500 | 1.000 |
| FR vs B1: detection_mutants | Wilcoxon | 90% vs 71% | 0.88 | 0.004 | 0.020 |
| FR-rules vs FR: error_rate | Wilcoxon | 23% vs 21% | 0.57 | 0.695 | 1.000 |
| FR-rules vs FR: detection_seeded | Wilcoxon | 77% vs 80% | 0.43 | 0.750 | 1.000 |
| FR-rules vs FR: detection_mutants | Wilcoxon | 87% vs 90% | 0.39 | 0.312 | 1.000 |

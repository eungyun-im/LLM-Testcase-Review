# Results

- `qwen2.5:7b` through the openai-compatible client: 30 runs, 2026-10-09 to 2026-10-09

## AEB-lite

### Table 1. Metrics by condition

| Condition | Runs | Tests | Rows rejected | Error rate | Boundary recall (simple / strict) | Input classes | Detection: seeded | Detection: mutants | LLM calls |
|---|---|---|---|---|---|---|---|---|---|
| B1 enhanced prompt | 10 | 33.3 ± 21.2 | 4.6 ± 12.0 | 43% ± 13% | 67% ± 17% / 56% ± 26% | 69% ± 16% | 59% ± 21% | 70% ± 15% | 1.0 ± 0.0 |
| FR feedback refinement | 10 | 45.9 ± 20.2 | 1.3 ± 3.8 | 18% ± 18% | 93% ± 21% / 81% ± 31% | 87% ± 18% | 77% ± 20% | 88% ± 18% | 8.2 ± 2.7 |
| FR, vote one test at a time, order given | 10 | 41.4 ± 20.5 | 3.0 ± 4.7 | 9% ± 5% | 93% ± 21% / 74% ± 34% | 81% ± 17% | 70% ± 21% | 84% ± 21% | 127.6 ± 61.9 |

### Table 2. Seeded defects detected (runs that detected / runs)

| Defect | Type | B0 | B1 | FR | H |
|---|---|---|---|---|---|
| F1 | boundary operator |  | 9/10 | 10/10 |  |
| F2 | boundary operator |  | 8/10 | 9/10 |  |
| F3 | boundary operator |  | 10/10 | 10/10 |  |
| F4 | missing check |  | 6/10 | 7/10 |  |
| F5 | null handling |  | 2/10 | 4/10 |  |
| F6 | check order |  | 5/10 | 8/10 |  |
| F7 | numeric conversion |  | 1/10 | 6/10 |  |

### Table 3. Statistical comparisons

| Comparison | Test | Means | A12 | p | p (Holm) |
|---|---|---|---|---|---|
| FR vs B1: error_rate | Wilcoxon | 18% vs 43% | 0.12 | 0.010 | 0.049 |
| FR vs B1: detection_seeded | Wilcoxon | 77% vs 59% | 0.77 | 0.031 | 0.125 |
| FR vs B1: detection_mutants | Wilcoxon | 88% vs 70% | 0.78 | 0.004 | 0.023 |
| FR-ordered vs FR: error_rate | Wilcoxon | 9% vs 18% | 0.28 | 0.160 | 0.480 |
| FR-ordered vs FR: detection_seeded | Wilcoxon | 70% vs 77% | 0.38 | 0.219 | 0.480 |
| FR-ordered vs FR: detection_mutants | Wilcoxon | 84% vs 88% | 0.47 | 0.500 | 0.500 |

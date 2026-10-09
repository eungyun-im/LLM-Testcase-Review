# Results

- `qwen2.5:3b` through the openai-compatible client: 80 runs, 2026-10-09 to 2026-10-09

## AEB-lite

### Table 1. Metrics by condition

| Condition | Runs | Tests | Rows rejected | Error rate | Boundary recall (simple / strict) | Input classes | Detection: seeded | Detection: mutants | LLM calls |
|---|---|---|---|---|---|---|---|---|---|
| B0 single shot | 10 | 9.9 ± 3.7 | 1.3 ± 2.6 | 47% ± 10% | 21% ± 8% / 17% ± 8% | 54% ± 24% | 27% ± 11% | 41% ± 15% | 1.0 ± 0.0 |
| B1 enhanced prompt | 10 | 20.1 ± 24.6 | 8.1 ± 10.2 | 39% ± 21% | 37% ± 18% / 24% ± 19% | 46% ± 25% | 36% ± 23% | 37% ± 19% | 1.0 ± 0.0 |
| FR feedback refinement | 10 | 23.6 ± 35.2 | 0.2 ± 0.6 | 53% ± 22% | 41% ± 26% / 28% ± 29% | 49% ± 30% | 41% ± 32% | 45% ± 28% | 5.7 ± 3.4 |
| FR without coverage feedback | 10 | 22.2 ± 24.5 | 0.3 ± 0.9 | 55% ± 23% | 37% ± 18% / 25% ± 19% | 47% ± 25% | 37% ± 27% | 38% ± 23% | 5.6 ± 2.2 |
| FR without cross-check | 10 | 21.8 ± 25.1 | 0.0 ± 0.0 | 41% ± 19% | 43% ± 27% / 24% ± 19% | 49% ± 28% | 36% ± 23% | 38% ± 20% | 2.1 ± 0.3 |
| FR without mutation feedback | 10 | 21.1 ± 27.6 | 0.4 ± 1.3 | 50% ± 23% | 37% ± 18% / 24% ± 19% | 46% ± 25% | 37% ± 25% | 39% ± 21% | 5.4 ± 2.5 |
| FR with ungrounded cross-check | 10 | 20.1 ± 24.6 | 0.0 ± 0.0 | 39% ± 20% | 37% ± 18% / 24% ± 19% | 46% ± 25% | 36% ± 22% | 38% ± 19% | 5.3 ± 2.2 |
| FR, model rewrites the set | 9 | 31.9 ± 21.1 | 8.0 ± 13.6 | 46% ± 26% | 64% ± 32% / 41% ± 20% | 70% ± 30% | 41% ± 22% | 47% ± 20% | 10.4 ± 8.0 |

### Table 2. Seeded defects detected (runs that detected / runs)

| Defect | Type | B0 | B1 | FR | H |
|---|---|---|---|---|---|
| F1 | boundary operator | 4/10 | 2/10 | 5/10 |  |
| F2 | boundary operator | 3/10 | 2/10 | 2/10 |  |
| F3 | boundary operator | 3/10 | 8/10 | 9/10 |  |
| F4 | missing check | 5/10 | 1/10 | 2/10 |  |
| F5 | null handling | 3/10 | 4/10 | 5/10 |  |
| F6 | check order | 1/10 | 8/10 | 5/10 |  |
| F7 | numeric conversion | 0/10 | 0/10 | 1/10 |  |

### Table 3. Statistical comparisons

| Comparison | Test | Means | A12 | p | p (Holm) |
|---|---|---|---|---|---|
| B0 vs B1: error_rate | Mann-Whitney | 47% vs 39% | 0.57 | 0.596 | 1.000 |
| B0 vs B1: detection_seeded | Mann-Whitney | 27% vs 36% | 0.39 | 0.379 | 1.000 |
| B0 vs B1: detection_mutants | Mann-Whitney | 41% vs 37% | 0.54 | 0.787 | 1.000 |
| FR vs B1: error_rate | Wilcoxon | 53% vs 39% | 0.73 | 0.039 | 0.781 |
| FR vs B1: detection_seeded | Wilcoxon | 41% vs 36% | 0.54 | 0.500 | 1.000 |
| FR vs B1: detection_mutants | Wilcoxon | 45% vs 37% | 0.57 | 0.094 | 1.000 |
| FR vs FR-coverage: error_rate | Wilcoxon | 53% vs 55% | 0.47 | 0.641 | 1.000 |
| FR vs FR-coverage: detection_seeded | Wilcoxon | 41% vs 37% | 0.54 | 0.562 | 1.000 |
| FR vs FR-coverage: detection_mutants | Wilcoxon | 45% vs 38% | 0.57 | 0.188 | 1.000 |
| FR vs FR-cross: error_rate | Wilcoxon | 53% vs 41% | 0.73 | 0.078 | 1.000 |
| FR vs FR-cross: detection_seeded | Wilcoxon | 41% vs 36% | 0.54 | 0.500 | 1.000 |
| FR vs FR-cross: detection_mutants | Wilcoxon | 45% vs 38% | 0.57 | 0.094 | 1.000 |
| FR vs FR-mutation: error_rate | Wilcoxon | 53% vs 50% | 0.57 | 0.625 | 1.000 |
| FR vs FR-mutation: detection_seeded | Wilcoxon | 41% vs 37% | 0.52 | 1.000 | 1.000 |
| FR vs FR-mutation: detection_mutants | Wilcoxon | 45% vs 39% | 0.55 | 0.250 | 1.000 |
| FR vs FR-self: error_rate | Wilcoxon | 53% vs 39% | 0.74 | 0.027 | 0.574 |
| FR vs FR-self: detection_seeded | Wilcoxon | 41% vs 36% | 0.54 | 0.578 | 1.000 |
| FR vs FR-self: detection_mutants | Wilcoxon | 45% vs 38% | 0.56 | 0.250 | 1.000 |
| FR vs FR-rewrite: error_rate | Wilcoxon | 52% vs 46% | 0.54 | 0.461 | 1.000 |
| FR vs FR-rewrite: detection_seeded | Wilcoxon | 43% vs 41% | 0.48 | 0.750 | 1.000 |
| FR vs FR-rewrite: detection_mutants | Wilcoxon | 46% vs 47% | 0.44 | 1.000 | 1.000 |

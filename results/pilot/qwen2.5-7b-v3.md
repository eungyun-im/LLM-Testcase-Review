# Results

- `qwen2.5:7b` through the openai-compatible client: 40 runs, 2026-10-09 to 2026-10-09

## AEB-lite

### Table 1. Metrics by condition

| Condition | Runs | Tests | Rows rejected | Error rate | Boundary recall (simple / strict) | Input classes | Detection: seeded | Detection: mutants | LLM calls |
|---|---|---|---|---|---|---|---|---|---|
| B0 single shot | 5 | 9.6 ± 1.5 | 0.6 ± 1.3 | 28% ± 11% | 24% ± 9% / 19% ± 12% | 71% ± 10% | 37% ± 13% | 55% ± 10% | 1.0 ± 0.0 |
| B1 enhanced prompt | 5 | 25.8 ± 13.6 | 7.2 ± 10.7 | 51% ± 10% | 59% ± 14% / 49% ± 17% | 71% ± 14% | 60% ± 26% | 63% ± 15% | 1.0 ± 0.0 |
| FR feedback refinement | 5 | 38.4 ± 11.8 | 3.6 ± 6.5 | 20% ± 3% | 93% ± 15% / 81% ± 17% | 94% ± 8% | 83% ± 6% | 88% ± 14% | 8.4 ± 1.5 |
| FR without coverage feedback | 5 | 31.0 ± 11.9 | 0.0 ± 0.0 | 17% ± 11% | 69% ± 12% / 61% ± 17% | 77% ± 16% | 71% ± 20% | 78% ± 20% | 6.2 ± 0.8 |
| FR without cross-check | 5 | 37.6 ± 9.2 | 1.8 ± 4.0 | 54% ± 9% | 95% ± 12% / 84% ± 20% | 94% ± 8% | 71% ± 23% | 78% ± 11% | 3.6 ± 0.5 |
| FR without mutation feedback | 5 | 35.2 ± 10.3 | 0.0 ± 0.0 | 21% ± 7% | 100% ± 0% / 88% ± 23% | 97% ± 6% | 89% ± 6% | 90% ± 14% | 6.2 ± 1.3 |
| FR with ungrounded cross-check | 5 | 38.6 ± 12.7 | 4.2 ± 4.3 | 49% ± 11% | 93% ± 15% / 77% ± 21% | 94% ± 8% | 77% ± 13% | 80% ± 13% | 7.4 ± 1.7 |
| FR, model rewrites the set | 5 | 41.8 ± 16.8 | 0.2 ± 0.4 | 55% ± 10% | 92% ± 11% / 71% ± 21% | 83% ± 16% | 66% ± 30% | 73% ± 20% | 14.2 ± 1.6 |

### Table 2. Seeded defects detected (runs that detected / runs)

| Defect | Type | B0 | B1 | FR | H |
|---|---|---|---|---|---|
| F1 | boundary operator | 2/5 | 5/5 | 5/5 |  |
| F2 | boundary operator | 1/5 | 3/5 | 4/5 |  |
| F3 | boundary operator | 2/5 | 5/5 | 5/5 |  |
| F4 | missing check | 4/5 | 1/5 | 3/5 |  |
| F5 | null handling | 0/5 | 2/5 | 4/5 |  |
| F6 | check order | 4/5 | 4/5 | 4/5 |  |
| F7 | numeric conversion | 0/5 | 1/5 | 4/5 |  |

### Table 3. Statistical comparisons

| Comparison | Test | Means | A12 | p | p (Holm) |
|---|---|---|---|---|---|
| B0 vs B1: error_rate | Mann-Whitney | 28% vs 51% | 0.00 | 0.012 | 0.250 |
| B0 vs B1: detection_seeded | Mann-Whitney | 37% vs 60% | 0.22 | 0.157 | 1.000 |
| B0 vs B1: detection_mutants | Mann-Whitney | 55% vs 63% | 0.30 | 0.334 | 1.000 |
| FR vs B1: error_rate | Wilcoxon | 20% vs 51% | 0.00 | 0.062 | 1.000 |
| FR vs B1: detection_seeded | Wilcoxon | 83% vs 60% | 0.76 | 0.250 | 1.000 |
| FR vs B1: detection_mutants | Wilcoxon | 88% vs 63% | 0.90 | 0.125 | 1.000 |
| FR vs FR-coverage: error_rate | Wilcoxon | 20% vs 17% | 0.60 | 0.812 | 1.000 |
| FR vs FR-coverage: detection_seeded | Wilcoxon | 83% vs 71% | 0.64 | 0.500 | 1.000 |
| FR vs FR-coverage: detection_mutants | Wilcoxon | 88% vs 78% | 0.66 | 1.000 | 1.000 |
| FR vs FR-cross: error_rate | Wilcoxon | 20% vs 54% | 0.00 | 0.062 | 1.000 |
| FR vs FR-cross: detection_seeded | Wilcoxon | 83% vs 71% | 0.66 | 0.375 | 1.000 |
| FR vs FR-cross: detection_mutants | Wilcoxon | 88% vs 78% | 0.74 | 0.125 | 1.000 |
| FR vs FR-mutation: error_rate | Wilcoxon | 20% vs 21% | 0.52 | 0.625 | 1.000 |
| FR vs FR-mutation: detection_seeded | Wilcoxon | 83% vs 89% | 0.32 | 0.500 | 1.000 |
| FR vs FR-mutation: detection_mutants | Wilcoxon | 88% vs 90% | 0.46 | 1.000 | 1.000 |
| FR vs FR-self: error_rate | Wilcoxon | 20% vs 49% | 0.00 | 0.062 | 1.000 |
| FR vs FR-self: detection_seeded | Wilcoxon | 83% vs 77% | 0.62 | 1.000 | 1.000 |
| FR vs FR-self: detection_mutants | Wilcoxon | 88% vs 80% | 0.70 | 0.250 | 1.000 |
| FR vs FR-rewrite: error_rate | Wilcoxon | 20% vs 55% | 0.00 | 0.062 | 1.000 |
| FR vs FR-rewrite: detection_seeded | Wilcoxon | 83% vs 66% | 0.72 | 0.500 | 1.000 |
| FR vs FR-rewrite: detection_mutants | Wilcoxon | 88% vs 73% | 0.76 | 0.125 | 1.000 |

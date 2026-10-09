# Results

- `qwen2.5:7b` through the openai-compatible client: 80 runs, 2026-10-09 to 2026-10-09

## AEB-lite

### Table 1. Metrics by condition

| Condition | Runs | Tests | Rows rejected | Error rate | Boundary recall (simple / strict) | Input classes | Detection: seeded | Detection: mutants | LLM calls |
|---|---|---|---|---|---|---|---|---|---|
| B0 single shot | 10 | 9.1 ± 1.5 | 1.0 ± 1.2 | 32% ± 10% | 23% ± 7% / 17% ± 7% | 70% ± 11% | 44% ± 16% | 53% ± 12% | 1.0 ± 0.0 |
| B1 enhanced prompt | 10 | 26.7 ± 9.7 | 2.7 ± 5.2 | 43% ± 21% | 67% ± 20% / 53% ± 22% | 70% ± 25% | 57% ± 19% | 58% ± 16% | 1.0 ± 0.0 |
| FR feedback refinement | 10 | 38.1 ± 13.5 | 2.3 ± 4.3 | 26% ± 15% | 97% ± 8% / 77% ± 22% | 83% ± 21% | 70% ± 21% | 87% ± 18% | 7.7 ± 2.3 |
| FR without coverage feedback | 10 | 32.0 ± 8.0 | 2.2 ± 4.2 | 27% ± 15% | 75% ± 12% / 61% ± 18% | 76% ± 24% | 70% ± 17% | 79% ± 16% | 6.0 ± 1.7 |
| FR without cross-check | 10 | 36.6 ± 6.4 | 3.0 ± 5.5 | 48% ± 17% | 97% ± 8% / 74% ± 22% | 87% ± 16% | 64% ± 15% | 69% ± 14% | 3.1 ± 0.7 |
| FR without mutation feedback | 10 | 35.4 ± 10.0 | 1.1 ± 3.5 | 27% ± 16% | 97% ± 8% / 70% ± 25% | 86% ± 22% | 71% ± 16% | 83% ± 18% | 7.1 ± 1.9 |
| FR with ungrounded cross-check | 10 | 38.2 ± 14.0 | 2.0 ± 4.3 | 47% ± 14% | 93% ± 21% / 75% ± 28% | 94% ± 12% | 69% ± 23% | 74% ± 15% | 7.1 ± 1.9 |
| FR, model rewrites the set | 10 | 63.7 ± 18.3 | 1.2 ± 2.5 | 55% ± 22% | 88% ± 26% / 62% ± 34% | 79% ± 18% | 57% ± 29% | 67% ± 25% | 19.6 ± 6.6 |

### Table 2. Seeded defects detected (runs that detected / runs)

| Defect | Type | B0 | B1 | FR | H |
|---|---|---|---|---|---|
| F1 | boundary operator | 4/10 | 6/10 | 10/10 |  |
| F2 | boundary operator | 4/10 | 5/10 | 9/10 |  |
| F3 | boundary operator | 4/10 | 9/10 | 9/10 |  |
| F4 | missing check | 9/10 | 3/10 | 6/10 |  |
| F5 | null handling | 0/10 | 4/10 | 5/10 |  |
| F6 | check order | 10/10 | 9/10 | 6/10 |  |
| F7 | numeric conversion | 0/10 | 4/10 | 4/10 |  |

### Table 3. Statistical comparisons

| Comparison | Test | Means | A12 | p | p (Holm) |
|---|---|---|---|---|---|
| B0 vs B1: error_rate | Mann-Whitney | 32% vs 43% | 0.34 | 0.225 | 1.000 |
| B0 vs B1: detection_seeded | Mann-Whitney | 44% vs 57% | 0.28 | 0.087 | 0.956 |
| B0 vs B1: detection_mutants | Mann-Whitney | 53% vs 58% | 0.36 | 0.299 | 1.000 |
| FR vs B1: error_rate | Wilcoxon | 26% vs 43% | 0.26 | 0.027 | 0.383 |
| FR vs B1: detection_seeded | Wilcoxon | 70% vs 57% | 0.72 | 0.051 | 0.660 |
| FR vs B1: detection_mutants | Wilcoxon | 87% vs 58% | 0.88 | 0.002 | 0.041 |
| FR vs FR-coverage: error_rate | Wilcoxon | 26% vs 27% | 0.49 | 0.625 | 1.000 |
| FR vs FR-coverage: detection_seeded | Wilcoxon | 70% vs 70% | 0.54 | 1.000 | 1.000 |
| FR vs FR-coverage: detection_mutants | Wilcoxon | 87% vs 79% | 0.65 | 0.062 | 0.750 |
| FR vs FR-cross: error_rate | Wilcoxon | 26% vs 48% | 0.18 | 0.004 | 0.074 |
| FR vs FR-cross: detection_seeded | Wilcoxon | 70% vs 64% | 0.65 | 0.219 | 1.000 |
| FR vs FR-cross: detection_mutants | Wilcoxon | 87% vs 69% | 0.80 | 0.002 | 0.041 |
| FR vs FR-mutation: error_rate | Wilcoxon | 26% vs 27% | 0.53 | 0.734 | 1.000 |
| FR vs FR-mutation: detection_seeded | Wilcoxon | 70% vs 71% | 0.49 | 1.000 | 1.000 |
| FR vs FR-mutation: detection_mutants | Wilcoxon | 87% vs 83% | 0.56 | 0.250 | 1.000 |
| FR vs FR-self: error_rate | Wilcoxon | 26% vs 47% | 0.15 | 0.006 | 0.105 |
| FR vs FR-self: detection_seeded | Wilcoxon | 70% vs 69% | 0.54 | 0.996 | 1.000 |
| FR vs FR-self: detection_mutants | Wilcoxon | 87% vs 74% | 0.74 | 0.018 | 0.281 |
| FR vs FR-rewrite: error_rate | Wilcoxon | 26% vs 55% | 0.12 | 0.014 | 0.232 |
| FR vs FR-rewrite: detection_seeded | Wilcoxon | 70% vs 57% | 0.62 | 0.188 | 1.000 |
| FR vs FR-rewrite: detection_mutants | Wilcoxon | 87% vs 67% | 0.78 | 0.021 | 0.322 |

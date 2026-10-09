# Results

- `qwen2.5:7b` through the openai-compatible client: 30 runs, 2026-10-09 to 2026-10-09

## AEB-lite

### Table 1. Metrics by condition

| Condition | Runs | Tests | Rows rejected | Error rate | Boundary recall (simple / strict) | Detection: seeded | Detection: mutants | LLM calls |
|---|---|---|---|---|---|---|---|---|
| B0 single shot | 5 | 10.2 ± 0.4 | 0.0 ± 0.0 | 45% ± 12% | 24% ± 8% / 23% ± 8% | 31% ± 12% | 42% ± 6% | 1.0 ± 0.0 |
| B1 enhanced prompt | 5 | 27.2 ± 12.5 | 7.6 ± 16.4 | 50% ± 13% | 64% ± 10% / 53% ± 24% | 51% ± 16% | 53% ± 15% | 1.0 ± 0.0 |
| FR feedback refinement | 5 | 41.8 ± 13.6 | 0.0 ± 0.0 | 52% ± 16% | 91% ± 17% / 72% ± 32% | 51% ± 26% | 65% ± 23% | 13.0 ± 0.0 |
| FR without boundary feedback | 5 | 45.8 ± 24.5 | 0.2 ± 0.4 | 57% ± 11% | 65% ± 6% / 55% ± 14% | 49% ± 19% | 60% ± 18% | 13.0 ± 0.0 |
| FR without cross-check | 5 | 33.8 ± 4.0 | 0.2 ± 0.4 | 55% ± 13% | 100% ± 0% / 76% ± 33% | 66% ± 13% | 80% ± 13% | 3.0 ± 1.0 |
| FR without mutation feedback | 5 | 65.2 ± 35.0 | 0.0 ± 0.0 | 56% ± 18% | 96% ± 6% / 67% ± 28% | 54% ± 19% | 68% ± 19% | 13.0 ± 0.0 |

### Table 2. Seeded defects detected (runs that detected / runs)

| Defect | Type | B0 | B1 | FR | H |
|---|---|---|---|---|---|
| F1 | boundary operator | 1/5 | 3/5 | 3/5 |  |
| F2 | boundary operator | 1/5 | 3/5 | 3/5 |  |
| F3 | boundary operator | 1/5 | 4/5 | 4/5 |  |
| F4 | missing check | 3/5 | 2/5 | 3/5 |  |
| F5 | null handling | 0/5 | 1/5 | 0/5 |  |
| F6 | check order | 5/5 | 4/5 | 3/5 |  |
| F7 | numeric conversion | 0/5 | 1/5 | 2/5 |  |

### Table 3. Statistical comparisons

| Comparison | Test | Means | A12 | p | p (Holm) |
|---|---|---|---|---|---|
| B0 vs B1: error_rate | Mann-Whitney | 45% vs 50% | 0.36 | 0.530 | 1.000 |
| B0 vs B1: detection_seeded | Mann-Whitney | 31% vs 51% | 0.16 | 0.086 | 1.000 |
| B0 vs B1: detection_mutants | Mann-Whitney | 42% vs 53% | 0.28 | 0.278 | 1.000 |
| FR vs B1: error_rate | Wilcoxon | 52% vs 50% | 0.48 | 0.812 | 1.000 |
| FR vs B1: detection_seeded | Wilcoxon | 51% vs 51% | 0.48 | 1.000 | 1.000 |
| FR vs B1: detection_mutants | Wilcoxon | 65% vs 53% | 0.70 | 0.250 | 1.000 |
| FR vs FR-boundary: error_rate | Wilcoxon | 52% vs 57% | 0.36 | 0.625 | 1.000 |
| FR vs FR-boundary: detection_seeded | Wilcoxon | 51% vs 49% | 0.54 | 0.750 | 1.000 |
| FR vs FR-boundary: detection_mutants | Wilcoxon | 65% vs 60% | 0.60 | 0.500 | 1.000 |
| FR vs FR-cross: error_rate | Wilcoxon | 52% vs 55% | 0.44 | 0.625 | 1.000 |
| FR vs FR-cross: detection_seeded | Wilcoxon | 51% vs 66% | 0.32 | 0.250 | 1.000 |
| FR vs FR-cross: detection_mutants | Wilcoxon | 65% vs 80% | 0.32 | 0.125 | 1.000 |
| FR vs FR-mutation: error_rate | Wilcoxon | 52% vs 56% | 0.44 | 0.812 | 1.000 |
| FR vs FR-mutation: detection_seeded | Wilcoxon | 51% vs 54% | 0.46 | 1.000 | 1.000 |
| FR vs FR-mutation: detection_mutants | Wilcoxon | 65% vs 68% | 0.46 | 0.812 | 1.000 |

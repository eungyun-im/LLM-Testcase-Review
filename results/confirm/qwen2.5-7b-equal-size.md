# Detection at equal test counts

Every test set is cut to the size of the smallest set of its repetition (100 random subsets each). Means over repetitions. B0 is left out: it is smaller by design.

| Condition | Tests, full set | Tests used | Detection: seeded, full | at equal size | Detection: mutants, full | at equal size |
|---|---|---|---|---|---|---|
| B1 enhanced prompt | 26.7 | 26.7 | 57% | 57% | 58% | 58% |
| FR feedback refinement | 38.1 | 26.7 | 70% | 62% | 87% | 78% |
| FR without coverage feedback | 32.0 | 26.7 | 70% | 65% | 79% | 75% |
| FR without cross-check | 36.6 | 26.7 | 64% | 55% | 69% | 63% |
| FR without mutation feedback | 35.4 | 26.7 | 71% | 63% | 83% | 77% |
| FR with ungrounded cross-check | 38.2 | 26.7 | 69% | 59% | 74% | 67% |
| FR, model rewrites the set | 63.7 | 26.7 | 57% | 38% | 67% | 52% |

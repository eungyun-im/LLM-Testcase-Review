# Detection at equal test counts

Every test set is cut to the size of the smallest set of its repetition (100 random subsets each). Means over repetitions. B0 is left out: it is smaller by design.

| Condition | Tests, full set | Tests used | Detection: seeded, full | at equal size | Detection: mutants, full | at equal size |
|---|---|---|---|---|---|---|
| B1 enhanced prompt | 24.3 | 24.3 | 73% | 73% | 71% | 71% |
| FR feedback refinement | 32.7 | 24.3 | 80% | 75% | 90% | 85% |
| FR, decision table instead of vote | 32.6 | 24.3 | 77% | 72% | 87% | 82% |

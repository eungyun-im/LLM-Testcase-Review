# Detection at equal test counts

Every test set is cut to the size of the smallest set of its repetition (100 random subsets each). Means over repetitions. B0 is left out: it is smaller by design.

| Condition | Tests, full set | Tests used | Detection: seeded, full | at equal size | Detection: mutants, full | at equal size |
|---|---|---|---|---|---|---|
| B1 enhanced prompt | 33.3 | 33.3 | 59% | 59% | 70% | 70% |
| FR feedback refinement | 45.9 | 33.3 | 77% | 68% | 88% | 81% |
| FR, vote one test at a time, order given | 41.4 | 33.3 | 70% | 65% | 84% | 80% |

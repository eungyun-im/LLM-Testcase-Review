# Detection at equal test counts

Every test set is cut to the size of the smallest set of its repetition (100 random subsets each). Means over repetitions. B0 is left out: it is smaller by design.

| Condition | Tests, full set | Tests used | Detection: seeded, full | at equal size | Detection: mutants, full | at equal size |
|---|---|---|---|---|---|---|
| B1 enhanced prompt | 22.3 | 19.4 | 40% | 39% | 41% | 40% |
| FR feedback refinement | 26.2 | 19.4 | 46% | 44% | 50% | 49% |
| FR without coverage feedback | 24.7 | 19.4 | 41% | 38% | 43% | 41% |
| FR without cross-check | 24.2 | 19.4 | 40% | 37% | 42% | 40% |
| FR without mutation feedback | 23.4 | 19.4 | 41% | 41% | 44% | 43% |
| FR with ungrounded cross-check | 22.3 | 19.4 | 40% | 39% | 42% | 42% |
| FR, model rewrites the set | 35.9 | 19.0 | 46% | 35% | 53% | 41% |

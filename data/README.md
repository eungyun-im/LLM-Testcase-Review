# Data

Two files here are filled in by a person. Everything else in the experiment is computed.

## human/aeb_baseline.csv

The human-designed test set, evaluated once as condition H.

- Same columns as generated test sets: `tc_id,req_id,speed_kph,obstacle_m,sensor_age_ms,expected`. Leave `obstacle_m` empty for "no obstacle detected".
- Design it from `requirements/aeb_requirements.yaml` with the same techniques the B1 prompt asks for: equivalence partitioning, boundary value analysis, decision table.
- Design it **before** reading `sut/defects.py` or the mutant list, and commit it before the first real run. A baseline written with the defects in view would be biased in its favor.

## mutants/equivalent.csv

Mutants judged equivalent, removed from the detection-rate denominator.

- An equivalent mutant changes the code without changing its behavior for any input, so no test can detect it.
- `python -m tcgen.mutation` lists every mutant and flags candidates that no probe input can tell from the reference. A candidate is a suggestion. The decision and its reason are recorded here.
- Columns: `mutant_id,equivalent,reason`, with `equivalent` set to `yes` or `no`.
- Current state: the probe grid distinguishes all 25 mutants, so there are no candidates.

## results.db

Created by `python -m tcgen.experiment`. Not committed.

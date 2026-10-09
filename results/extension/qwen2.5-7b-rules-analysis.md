# Error analysis

## Where the expected results are wrong

Final test sets of all repetitions, by input class.

**B1** (243 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 2 | 1% | 0% (0 of 2) |  |
| speed above the valid range | 9 | 4% | 11% (1 of 9) | NO_ACTION instead of FAULT |
| valid speed, sensor data 200 ms old or older | 91 | 37% | 54% (49 of 91) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 63 | 26% | 29% (18 of 63) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 14 | 6% | 57% (8 of 14) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 11 | 5% | 55% (6 of 11) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 53 | 22% | 49% (26 of 53) | NO_ACTION instead of BRAKE |

**FR** (327 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 11 | 3% | 0% (0 of 11) |  |
| speed above the valid range | 17 | 5% | 6% (1 of 17) | BRAKE instead of FAULT |
| valid speed, sensor data 200 ms old or older | 117 | 36% | 43% (50 of 117) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 78 | 24% | 10% (8 of 78) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 17 | 5% | 6% (1 of 17) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 16 | 5% | 44% (7 of 16) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 71 | 22% | 6% (4 of 71) | FAULT instead of BRAKE |

## The final vote of the additive procedure

The expected results of these runs are the majority of the votes below, so the share of the majority that is right is one minus the error rate.

| Condition | Tests voted on | Single votes right | Majority exists | Majority right | Unanimous | Unanimous right |
|---|---|---|---|---|---|---|
| FR | 327 | 78% (742 of 956) | 95% (311 of 327) | 80% (249 of 311) | 69% (224 of 327) | 88% (197 of 224) |

## The decision tables written by the model

Each table is graded on the probe inputs around every boundary, against the reference. Per table, not per test.

| Question | Answer |
|---|---|
| Tables requested | 30 |
| Unusable as written | 73% (22 of 30) |
| Usable tables that decide every probe correctly | 0% (0 of 8) |
| Mean share of probes decided wrongly, per usable table | 27.9% |
| Chosen tables (one per run) that decide every probe correctly | 0% (0 of 6) |

# Error analysis

## Where the expected results are wrong

Final test sets of all repetitions, by input class.

**B0** (48 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 4 | 8% | 0% (0 of 4) |  |
| speed above the valid range | 4 | 8% | 0% (0 of 4) |  |
| valid speed, sensor data 200 ms old or older | 6 | 12% | 17% (1 of 6) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 19 | 40% | 26% (5 of 19) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 0 | 0% | n/a |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 3 | 6% | 100% (3 of 3) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 12 | 25% | 42% (5 of 12) | FAULT instead of BRAKE |

**B1** (129 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 2 | 2% | 0% (0 of 2) |  |
| speed above the valid range | 5 | 4% | 0% (0 of 5) |  |
| valid speed, sensor data 200 ms old or older | 55 | 43% | 67% (37 of 55) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 31 | 24% | 35% (11 of 31) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 9 | 7% | 67% (6 of 9) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 4 | 3% | 50% (2 of 4) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 23 | 18% | 35% (8 of 23) | NO_ACTION instead of BRAKE |

**FR** (192 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 4 | 2% | 0% (0 of 4) |  |
| speed above the valid range | 9 | 5% | 11% (1 of 9) | BRAKE instead of FAULT |
| valid speed, sensor data 200 ms old or older | 66 | 34% | 33% (22 of 66) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 51 | 27% | 22% (11 of 51) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 14 | 7% | 7% (1 of 14) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 11 | 6% | 27% (3 of 11) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 37 | 19% | 3% (1 of 37) | NO_ACTION instead of BRAKE |

**FR-self** (193 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 4 | 2% | 0% (0 of 4) |  |
| speed above the valid range | 8 | 4% | 0% (0 of 8) |  |
| valid speed, sensor data 200 ms old or older | 74 | 38% | 50% (37 of 74) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 46 | 24% | 43% (20 of 46) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 15 | 8% | 67% (10 of 15) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 11 | 6% | 64% (7 of 11) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 35 | 18% | 51% (18 of 35) | NO_ACTION instead of BRAKE |

## The final vote of the additive procedure

The expected results of these runs are the majority of the votes below, so the share of the majority that is right is one minus the error rate.

| Condition | Tests voted on | Single votes right | Majority exists | Majority right | Unanimous | Unanimous right |
|---|---|---|---|---|---|---|
| FR | 192 | 77% (421 of 545) | 98% (189 of 192) | 80% (151 of 189) | 64% (122 of 192) | 85% (104 of 122) |
| FR-coverage | 155 | 79% (367 of 462) | 100% (155 of 155) | 80% (124 of 155) | 79% (122 of 155) | 86% (105 of 122) |
| FR-mutation | 176 | 77% (396 of 516) | 99% (175 of 176) | 79% (138 of 175) | 71% (125 of 176) | 86% (108 of 125) |
| FR-self | 193 | 52% (301 of 577) | 98% (190 of 193) | 53% (101 of 190) | 84% (162 of 193) | 54% (88 of 162) |

## The grounded cross-check as a detector of wrong expected results

Every round that ran it: 370 test results voted on, 3 votes each.

| Question | Answer |
|---|---|
| Stated expected results that were wrong | 52% (193 of 370) |
| Single votes that were right | 85% (937 of 1102) |
| Wrong results that were flagged (recall) | 91% (176 of 193) |
| Flagged results that were really wrong (precision) | 89% (176 of 198) |
| Flags whose proposed result was the right one | 86% (170 of 198) |
| Results confirmed by all 3 votes | 40% (147 of 370) |
| Confirmed results that were right | 95% (139 of 147) |

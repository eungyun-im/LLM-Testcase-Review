# Error analysis

## Where the expected results are wrong

Final test sets of all repetitions, by input class.

**B0** (20 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 2 | 10% | 0% (0 of 2) |  |
| speed above the valid range | 2 | 10% | 0% (0 of 2) |  |
| valid speed, sensor data 200 ms old or older | 4 | 20% | 25% (1 of 4) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 8 | 40% | 38% (3 of 8) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 0 | 0% | n/a |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 0 | 0% | n/a |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 4 | 20% | 25% (1 of 4) | FAULT instead of BRAKE |

**B1** (115 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 2 | 2% | 0% (0 of 2) |  |
| speed above the valid range | 4 | 3% | 0% (0 of 4) |  |
| valid speed, sensor data 200 ms old or older | 49 | 43% | 67% (33 of 49) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 37 | 32% | 14% (5 of 37) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 6 | 5% | 17% (1 of 6) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 4 | 3% | 50% (2 of 4) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 13 | 11% | 77% (10 of 13) | NO_ACTION instead of BRAKE |

**FR** (56 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 2 | 4% | 0% (0 of 2) |  |
| speed above the valid range | 2 | 4% | 0% (0 of 2) |  |
| valid speed, sensor data 200 ms old or older | 21 | 38% | 57% (12 of 21) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 21 | 38% | 19% (4 of 21) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 0 | 0% | n/a |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 1 | 2% | 0% (0 of 1) |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 9 | 16% | 78% (7 of 9) | NO_ACTION instead of BRAKE |

**FR-self** (18 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 0 | 0% | n/a |  |
| speed above the valid range | 0 | 0% | n/a |  |
| valid speed, sensor data 200 ms old or older | 14 | 78% | 71% (10 of 14) | BRAKE instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 0 | 0% | n/a |  |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 0 | 0% | n/a |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 3 | 17% | 33% (1 of 3) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 1 | 6% | 0% (0 of 1) |  |

## The ungrounded cross-check as a detector of wrong expected results

Every round that ran it: 43 test results voted on, 3 votes each.

| Question | Answer |
|---|---|
| Stated expected results that were wrong | 35% (15 of 43) |
| Single votes that were right | 53% (68 of 129) |
| Wrong results that were flagged (recall) | 27% (4 of 15) |
| Flagged results that were really wrong (precision) | 36% (4 of 11) |
| Flags whose proposed result was the right one | 9% (1 of 11) |
| Results confirmed by all 3 votes | 70% (30 of 43) |
| Confirmed results that were right | 67% (20 of 30) |

## The grounded cross-check as a detector of wrong expected results

Every round that ran it: 820 test results voted on, 3 votes each.

| Question | Answer |
|---|---|
| Stated expected results that were wrong | 39% (323 of 820) |
| Single votes that were right | 78% (1901 of 2442) |
| Wrong results that were flagged (recall) | 93% (302 of 323) |
| Flagged results that were really wrong (precision) | 73% (302 of 414) |
| Flags whose proposed result was the right one | 66% (275 of 414) |
| Results confirmed by all 3 votes | 37% (306 of 820) |
| Confirmed results that were right | 94% (288 of 306) |

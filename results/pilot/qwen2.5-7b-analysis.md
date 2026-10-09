# Error analysis

## Where the expected results are wrong

Final test sets of all repetitions, by input class.

**B0** (51 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 1 | 2% | 0% (0 of 1) |  |
| speed above the valid range | 3 | 6% | 0% (0 of 3) |  |
| valid speed, sensor data 200 ms old or older | 13 | 25% | 54% (7 of 13) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 14 | 27% | 29% (4 of 14) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 0 | 0% | n/a |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 4 | 8% | 75% (3 of 4) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 16 | 31% | 56% (9 of 16) | NO_ACTION instead of BRAKE |

**B1** (136 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 0 | 0% | n/a |  |
| speed above the valid range | 3 | 2% | 0% (0 of 3) |  |
| valid speed, sensor data 200 ms old or older | 74 | 54% | 59% (44 of 74) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 25 | 18% | 32% (8 of 25) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 3 | 2% | 0% (0 of 3) |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 4 | 3% | 25% (1 of 4) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 27 | 20% | 74% (20 of 27) | NO_ACTION instead of BRAKE |

**FR** (209 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 7 | 3% | 0% (0 of 7) |  |
| speed above the valid range | 12 | 6% | 17% (2 of 12) | NO_ACTION instead of FAULT |
| valid speed, sensor data 200 ms old or older | 95 | 45% | 72% (68 of 95) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 52 | 25% | 19% (10 of 52) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 0 | 0% | n/a |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 12 | 6% | 17% (2 of 12) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 31 | 15% | 71% (22 of 31) | NO_ACTION instead of BRAKE |

## The ungrounded cross-check as a detector of wrong expected results

Every round that ran it: 1801 test results voted on, 3 votes each.

| Question | Answer |
|---|---|
| Stated expected results that were wrong | 57% (1034 of 1801) |
| Single votes that were right | 45% (2268 of 5088) |
| Wrong results that were flagged (recall) | 45% (462 of 1034) |
| Flagged results that were really wrong (precision) | 65% (462 of 714) |
| Flags whose proposed result was the right one | 39% (277 of 714) |
| Results confirmed by all 3 votes | 41% (742 of 1801) |
| Confirmed results that were right | 54% (398 of 742) |

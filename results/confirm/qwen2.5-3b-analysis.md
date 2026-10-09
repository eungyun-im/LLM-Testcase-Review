# Error analysis

## Where the expected results are wrong

Final test sets of all repetitions, by input class.

**B0** (99 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 7 | 7% | 14% (1 of 7) | NO_ACTION instead of FAULT |
| speed above the valid range | 6 | 6% | 0% (0 of 6) |  |
| valid speed, sensor data 200 ms old or older | 20 | 20% | 55% (11 of 20) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 24 | 24% | 25% (6 of 24) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 7 | 7% | 29% (2 of 7) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 0 | 0% | n/a |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 35 | 35% | 77% (27 of 35) | FAULT instead of BRAKE |

**B1** (201 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 2 | 1% | 0% (0 of 2) |  |
| speed above the valid range | 5 | 2% | 0% (0 of 5) |  |
| valid speed, sensor data 200 ms old or older | 115 | 57% | 51% (59 of 115) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 24 | 12% | 25% (6 of 24) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 21 | 10% | 52% (11 of 21) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 1 | 0% | 100% (1 of 1) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 33 | 16% | 91% (30 of 33) | NO_ACTION instead of BRAKE |

**FR** (236 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 3 | 1% | 33% (1 of 3) | NO_ACTION instead of FAULT |
| speed above the valid range | 8 | 3% | 0% (0 of 8) |  |
| valid speed, sensor data 200 ms old or older | 122 | 52% | 73% (89 of 122) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 37 | 16% | 38% (14 of 37) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 23 | 10% | 39% (9 of 23) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 2 | 1% | 50% (1 of 2) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 41 | 17% | 63% (26 of 41) | NO_ACTION instead of BRAKE |

**FR-self** (201 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 2 | 1% | 0% (0 of 2) |  |
| speed above the valid range | 5 | 2% | 0% (0 of 5) |  |
| valid speed, sensor data 200 ms old or older | 115 | 57% | 52% (60 of 115) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 24 | 12% | 21% (5 of 24) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 21 | 10% | 76% (16 of 21) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 1 | 0% | 0% (0 of 1) |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 33 | 16% | 79% (26 of 33) | NO_ACTION instead of BRAKE |

## The final vote of the additive procedure

The expected results of these runs are the majority of the votes below, so the share of the majority that is right is one minus the error rate.

| Condition | Tests voted on | Single votes right | Majority exists | Majority right | Unanimous | Unanimous right |
|---|---|---|---|---|---|---|
| FR | 236 | 44% (295 of 666) | 89% (209 of 236) | 42% (87 of 209) | 42% (99 of 236) | 55% (54 of 99) |
| FR-coverage | 222 | 43% (230 of 540) | 71% (157 of 222) | 40% (63 of 157) | 35% (77 of 222) | 47% (36 of 77) |
| FR-mutation | 211 | 39% (220 of 569) | 85% (179 of 211) | 40% (71 of 179) | 45% (96 of 211) | 36% (35 of 96) |
| FR-self | 201 | 47% (273 of 575) | 96% (192 of 201) | 48% (93 of 192) | 55% (110 of 201) | 57% (63 of 110) |

## The grounded cross-check as a detector of wrong expected results

Every round that ran it: 153 test results voted on, 3 votes each.

| Question | Answer |
|---|---|
| Stated expected results that were wrong | 49% (75 of 153) |
| Single votes that were right | 48% (219 of 457) |
| Wrong results that were flagged (recall) | 56% (42 of 75) |
| Flagged results that were really wrong (precision) | 57% (42 of 74) |
| Flags whose proposed result was the right one | 41% (30 of 74) |
| Results confirmed by all 3 votes | 27% (42 of 153) |
| Confirmed results that were right | 62% (26 of 42) |

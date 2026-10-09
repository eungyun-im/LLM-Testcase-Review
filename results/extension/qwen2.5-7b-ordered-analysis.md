# Error analysis

## Where the expected results are wrong

Final test sets of all repetitions, by input class.

**B1** (333 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 4 | 1% | 0% (0 of 4) |  |
| speed above the valid range | 18 | 5% | 11% (2 of 18) | NO_ACTION instead of FAULT |
| valid speed, sensor data 200 ms old or older | 90 | 27% | 57% (51 of 90) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 109 | 33% | 28% (31 of 109) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 9 | 3% | 56% (5 of 9) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 17 | 5% | 59% (10 of 17) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 86 | 26% | 72% (62 of 86) | NO_ACTION instead of BRAKE |

**FR** (459 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 11 | 2% | 9% (1 of 11) | NO_ACTION instead of FAULT |
| speed above the valid range | 26 | 6% | 15% (4 of 26) | BRAKE instead of FAULT |
| valid speed, sensor data 200 ms old or older | 136 | 30% | 39% (53 of 136) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 145 | 32% | 13% (19 of 145) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 15 | 3% | 13% (2 of 15) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 24 | 5% | 29% (7 of 24) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 102 | 22% | 2% (2 of 102) | FAULT instead of BRAKE |

## The final vote of the additive procedure

The expected results of these runs are the majority of the votes below, so the share of the majority that is right is one minus the error rate.

| Condition | Tests voted on | Single votes right | Majority exists | Majority right | Unanimous | Unanimous right |
|---|---|---|---|---|---|---|
| FR | 459 | 82% (1097 of 1340) | 97% (443 of 459) | 83% (366 of 443) | 80% (369 of 459) | 88% (326 of 369) |
| FR-ordered | 414 | 89% (1106 of 1242) | 99% (410 of 414) | 91% (375 of 410) | 82% (339 of 414) | 97% (330 of 339) |

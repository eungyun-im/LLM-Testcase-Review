# Error analysis

## Where the expected results are wrong

Final test sets of all repetitions, by input class.

**B0** (91 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 6 | 7% | 0% (0 of 6) |  |
| speed above the valid range | 9 | 10% | 0% (0 of 9) |  |
| valid speed, sensor data 200 ms old or older | 16 | 18% | 31% (5 of 16) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 38 | 42% | 45% (17 of 38) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 0 | 0% | n/a |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 4 | 4% | 100% (4 of 4) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 18 | 20% | 22% (4 of 18) | FAULT instead of BRAKE |

**B1** (267 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 4 | 1% | 0% (0 of 4) |  |
| speed above the valid range | 10 | 4% | 20% (2 of 10) | NO_ACTION instead of FAULT |
| valid speed, sensor data 200 ms old or older | 121 | 45% | 60% (72 of 121) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 60 | 22% | 17% (10 of 60) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 8 | 3% | 50% (4 of 8) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 18 | 7% | 61% (11 of 18) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 46 | 17% | 52% (24 of 46) | NO_ACTION instead of BRAKE |

**FR** (381 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 14 | 4% | 0% (0 of 14) |  |
| speed above the valid range | 20 | 5% | 10% (2 of 20) | NO_ACTION instead of FAULT |
| valid speed, sensor data 200 ms old or older | 171 | 45% | 37% (64 of 171) | BRAKE instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 84 | 22% | 23% (19 of 84) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 13 | 3% | 0% (0 of 13) |  |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 19 | 5% | 58% (11 of 19) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 60 | 16% | 3% (2 of 60) | NO_ACTION instead of BRAKE |

**FR-self** (382 tests)

| Input class | Tests | Share of all tests | Wrong | Most common mistake |
|---|---|---|---|---|
| speed below the valid range | 14 | 4% | 0% (0 of 14) |  |
| speed above the valid range | 20 | 5% | 5% (1 of 20) | NO_ACTION instead of FAULT |
| valid speed, sensor data 200 ms old or older | 177 | 46% | 58% (103 of 177) | NO_ACTION instead of FAULT |
| valid speed below 30 km/h, fresh sensor data | 78 | 20% | 29% (23 of 78) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, no obstacle detected | 16 | 4% | 62% (10 of 16) | FAULT instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle farther than 20 m | 22 | 6% | 45% (10 of 22) | BRAKE instead of NO_ACTION |
| valid speed of at least 30 km/h, fresh sensor data, obstacle within 20 m | 55 | 14% | 69% (38 of 55) | NO_ACTION instead of BRAKE |

## The grounded cross-check as a detector of wrong expected results

Every round that ran it: 422 test results voted on, 3 votes each.

| Question | Answer |
|---|---|
| Stated expected results that were wrong | 53% (222 of 422) |
| Single votes that were right | 71% (894 of 1255) |
| Wrong results that were flagged (recall) | 76% (168 of 222) |
| Flagged results that were really wrong (precision) | 80% (168 of 210) |
| Flags whose proposed result was the right one | 69% (144 of 210) |
| Results confirmed by all 3 votes | 43% (181 of 422) |
| Confirmed results that were right | 78% (142 of 181) |

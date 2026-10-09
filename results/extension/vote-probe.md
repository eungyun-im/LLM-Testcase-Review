# Probe: how to ask the grounded vote

`qwen2.5:7b`, 2026-10-09. The same 120 tests, a random sample of the final FR test sets of
`results/confirm/qwen2.5-7b.db`. One run of each, so about 4 percentage points either way.
The way of asking was chosen after the confirmation run: exploratory.

`python tools/probe_vote_ways.py qwen2.5:7b`

| Way of asking | Votes right |
|---|---|
| 40 tests in one question (the confirmation run) | 70 % |
| 5 tests in one question | 76 % |
| One test per question | 83 % |
| One test per question, step by step | 72 % |
| One test per question, step by step, order of the requirements given | 88 % |

`python tools/probe_vote_majority.py qwen2.5:7b` (order of the requirements given, three votes per test)

| Answer | Single vote | Majority of three | Unanimous | Unanimous and right |
|---|---|---|---|---|
| Output only | 93 % | 94 % | 92 % of tests | 96 % |
| Step by step | 89 % | 89 % | 79 % of tests | 99 % |

Step by step did not help: reasoning at this model size adds mistakes as often as it removes them.

## Probe: temperature and number of votes

`python tools/probe_vote_settings.py qwen2.5:7b DB CONDITION TEMPERATURE VOTES [N]`. The vote is the ordered one
(one test per question, order of the requirements given). "Default" is the sampling of the server, which is not
sent. The same setting measured twice differs by up to 3 points (default, 3 votes, 120 tests: 93 % and 94 % in the
first probe above, 95 % and 97.5 % in this one).

**Tuning sample:** 120 tests, a random sample of the final FR test sets of `results/confirm/qwen2.5-7b.db`.

| Temperature | Votes | Single vote right | Majority right | Unanimous | Unanimous and right |
|---|---|---|---|---|---|
| default | 3 | 95.0 % | 97.5 % | 88 % | 100 % |
| 0 | 1 | 95.8 % | 95.8 % | 100 % | 95.8 % |
| 0.3 | 3 | 96.9 % | 96.7 % | 98 % | 98.3 % |
| 0.6 | 3 | 96.1 % | 95.0 % | 95 % | 99.1 % |
| default | 5 | 95.5 % | 96.7 % | 89 % | 100 % |
| 0.3 | 5 | 97.0 % | 96.7 % | 98 % | 98.3 % |

**Validation sample:** 300 tests drawn from `results/extension/qwen2.5-7b-ordered.db` (the tests of the ordered run, a
different and harder collection: the default setting is at 89 % here, which is what that run measured).

| Temperature | Votes | Single vote right | Majority right | Unanimous | Unanimous and right |
|---|---|---|---|---|---|
| default | 3 | 89.2 % | 91.0 % | 80 % | 97.9 % |
| 0 | 1 | 96.0 % | 96.0 % | 100 % | 96.0 % |
| 0.1 | 3 | 96.2 % | 96.0 % | 98 % | 97.3 % |
| **0.3** | **3** | **95.3 %** | **95.7 %** | **95 %** | **97.5 %** |
| 0.3 | 5 | 95.4 % | 96.0 % | 92 % | 98.6 % |

What it says: a low temperature is what helps, from about 89 % to 96 %. More votes add little, because the remaining
mistakes are systematic and not random. Temperature 0 gives the same accuracy with one vote, but then there is no
disagreement left to point at the doubtful tests. Temperature 0.3 with three votes keeps both.

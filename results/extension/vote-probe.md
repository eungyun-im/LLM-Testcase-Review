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

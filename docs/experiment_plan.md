# Plan of the full experiment

Draft of 2026-10-09, written after three pilots and before any run of the full
experiment. To be reviewed with the advisor, then frozen: after the first run
of the full experiment, nothing below changes without a dated note here.

## Question

Does deciding the atomic conditions of the requirements by a program, and
letting the model only apply the requirements to them, lower the share of wrong
expected results in LLM-written test cases, compared with letting the model
check itself?

## Hypotheses

| | Hypothesis | Primary comparison | Metric |
|---|---|---|---|
| H1 | The grounded vote gives a lower error rate than the ungrounded vote | FR vs FR with ungrounded cross-check, paired | Error rate |
| H2 | Applying the vote directly gives a lower error rate than letting the model rewrite the set | FR vs FR, model rewrites the set, paired | Error rate |
| H3 | The effect of grounding shrinks as the model gets better at the comparisons itself | H1 effect size, across models | A12 per model |

Secondary, reported without a claim: detection rates, boundary recall, input
class coverage, calls per final test set, the ablations.

## Design

| | |
|---|---|
| Models | Three, of different size: one small local model (the pilot model), one mid-size model, one large commercial model. Named with version and date before the run |
| Repetitions | 10 per condition and model. Raised to 20 if the pilot variance makes 10 too few for H1 (see power below) |
| Conditions | B0, B1, FR, the three ablations, FR with ungrounded cross-check, FR with rewrite, H |
| Systems | AEB-lite decision function. A second, stateful system is a stretch goal and reported separately |
| Human baseline | Designed by a person from the requirements, before looking at the defect list. A draft written by an AI assistant exists in `data/human/aeb_baseline_draft.csv`; it is not a human baseline and is not used as one |
| Equal-size comparison | Every test set is also scored on random subsets of the size of the smallest set in its repetition (100 draws) |

## Analysis

- Paired comparisons within a repetition: Wilcoxon signed-rank. Effect size: Vargha-Delaney A12.
- Holm correction over the three primary comparisons per model. Secondary comparisons are descriptive.
- A run that fails (truncated output, refusal) is reported as failed and counted. It is not rerun.
- Power: with five pairs the smallest possible p is 0.0625, so five repetitions can never reach 0.05. Ten pairs that all point the same way give p = 0.002.

## What is excluded on purpose

- The three pilots. They were used to design the method, so they cannot test it. They are reported as preliminary work.
- Any change to prompts, parser rules or checks after the first run of the full experiment.

## Threats that this design does not remove

- One system, stateless.
- The structured spec (6 conditions, 7 input classes) was written by the person who also wrote the reference implementation.
- The parser rules were set while reading the pilot model's output.

## Log

- **2026-10-09, confirmation run on `qwen2.5:7b`.** Run at commit `e8f63dd` with the design above, 10 repetitions, 80 runs, none failed. Results in `results/confirm/`. H1 and H2 hold: error rate 25.5 % against 46.6 % (p = 0.006, Holm 0.012) and against 54.5 % (p = 0.014, Holm 0.014). Holm was applied over the two comparisons that exist for one model; the third primary comparison (H3) needs several models. The pilots had overstated the effect (20 %).
- **2026-10-09, `qwen2.5:3b`.** Same commit, 10 repetitions, 80 runs, one failed. The method does not lower the error rate for this model (53 % against 39 % for the starting set): its votes are right 44 % of the time. H1 and H2 are not supported for this model, and are not tested again after the fact. The effect of grounding needs a model that can apply the rules.
- **2026-10-09, correction.** An earlier version of the README compared the accuracy of votes from different populations (rewrite loop in one run, additive procedure in the other) and reported a drop of a single vote from 85 % to 71 %. For the votes that decide the expected results it is 77 % in the third pilot and 74 % in the confirmation. `python -m tcgen.analysis` now grades both populations separately.
- Added after the confirmation run, outside the frozen design and reported as such: `tcgen/equal_size.py` (the equal-size comparison named above) and `tools/result_figures.py`.
- **2026-10-09, after the confirmation run: how the vote is asked.** Probes on 120 tests showed that asking one test at a time, with the order of the requirements given, takes the votes of `qwen2.5:7b` from 70 % to 93 % right. This was implemented as `FR-ordered` with a `priority` list in the spec, and run for 10 repetitions: error rate 9 % against 43 % for B1 (10 of 10 repetitions, p = 0.002) and 18 % for the frozen method (8 of 10, p = 0.16). It was chosen after seeing the confirmation data, so it is exploratory. **Before the next confirmation, the design should be frozen again with this condition as the proposed method**, and tested on more than one model.
- **2026-10-09, decision table.** `FR-rules` (the model writes decision rules once, a program applies them) did not help `qwen2.5:7b` (23 % against 21 %) and could not be used with `qwen2.5:3b`. Reported as a negative result.

## Design v2 (frozen before its run, 2026-10-09)

Written after the confirmation run, the analysis of its errors and the probes in `results/extension/vote-probe.md`.
It is frozen by the commit that contains this section; the run that tests it starts from that commit, and the commit is
named in the README. Nothing below is changed after the run has started without a dated note.

**Method (the proposed method is now FR-ordered).** The model extends the test set. The expected results are the
majority of three votes, each asked about one test, with the decided conditions and the order of the requirements given.
All conditions of the run use the sampling temperature 0.3, so that the comparison is not between settings.

**Conditions.** B0, B1, FR (the grounded vote of the first design, 40 tests per question), FR-cross (extended, results
as the model wrote them), FR-self (vote on the raw values), FR-rewrite (the model rewrites the set), FR-ordered.

**Model and repetitions.** `qwen2.5:7b`, 10 repetitions. A second model, `qwen2.5:3b`, for the question of whether
the method needs a model that can apply the rules; the 3b run is descriptive, not a test of the hypotheses.

| | Hypothesis | Comparison | Metric |
|---|---|---|---|
| H1' | The ordered vote gives a lower error rate than the grounded vote asked 40 tests at a time | FR-ordered vs FR, paired | Error rate |
| H2' | The method gives a lower error rate than the starting set | FR-ordered vs B1, paired | Error rate |
| T | The method reaches an error rate of at most 6 % on average (the user's mark of "usable" is about 96 % right) | FR-ordered, mean over repetitions | Error rate |

Holm over H1' and H2'. T is a target, reported as met or not met, without a p-value. Secondary and reported without a
claim: detection rates, input class coverage, calls, the share of tests on which all votes agree and how often those are
right, the other conditions.

**What this design does not remove.** One system, stateless. The structured spec (6 conditions, 7 input classes and the
order of the requirements) is more structure than the first design had, and was written by the person who also wrote
the reference. The temperature and the way of asking were chosen on tests of the earlier runs, and checked on a second
sample of them, not on fresh ones: the run of v2 is the first on fresh generations. No human-designed baseline yet.

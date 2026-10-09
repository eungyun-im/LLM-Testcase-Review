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

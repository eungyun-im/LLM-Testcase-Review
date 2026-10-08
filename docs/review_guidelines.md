# Review guidelines

One decision per candidate: `accept`, `fix`, or `reject`.

## Before deciding

1. Read the requirement text, not the rationale attached to the candidate.
2. Work out the expected result yourself, then compare.
3. Check the automatic check output for the candidate.

## Reason codes

| Code | Use when |
|---|---|
| `wrong_expected` | Expected result contradicts the requirement |
| `missed_boundary` | Value is near a threshold but not on the just-below / at / just-above points |
| `duplicate` | Same inputs and expected result as another case |
| `not_in_requirement` | Tests behavior the requirement does not state |
| `untestable` | Inputs or expected result cannot be observed or set |

## After review

Write any case the LLM failed to produce and mark it as human-added.

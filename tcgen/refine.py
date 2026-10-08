"""Feedback refinement (FR): repair a test set with automatic check results.

Starts from an existing test set (the B1 output of the same repetition) and
runs up to MAX_ROUNDS rounds. A round runs the enabled checks, and if any of
them found something, asks the model for a revised test set.
"""

from tcgen.checks import boundary_check, cross_check, mutation_check, render_feedback
from tcgen.generate import load_prompt
from tcgen.schema import parse_csv, to_csv

MAX_ROUNDS = 3
ALL_CHECKS = frozenset({"boundary", "cross", "mutation"})


def refine(llm, spec, tests, feedback_mutants, code_under_test, enabled=ALL_CHECKS, max_rounds=MAX_ROUNDS):
    """Return (tests, format_errors, calls, rounds_used)."""
    calls, format_errors, rounds_used = [], 0, 0
    for round_number in range(1, max_rounds + 1):
        missing = boundary_check(tests, spec) if "boundary" in enabled else []
        flagged = {}
        if "cross" in enabled:
            flagged, vote_calls = cross_check(tests, llm, spec)
            calls += [dict(call, round=round_number) for call in vote_calls]
        survivors = (
            mutation_check(tests, feedback_mutants, code_under_test) if "mutation" in enabled else []
        )
        feedback = render_feedback(missing, flagged, survivors)
        if not feedback:
            break
        prompt = load_prompt("feedback").format(
            requirements=spec.requirement_text(),
            inputs=spec.input_text(),
            outputs=", ".join(spec.outputs),
            tests=to_csv(tests),
            feedback=feedback,
        )
        meta = {"tests": tests, "missing": missing, "flagged": flagged, "survivors": survivors}
        response = llm.complete(prompt, kind="feedback", meta=meta)
        calls.append({"round": round_number, "kind": "feedback", "prompt": prompt, "response": response})
        rounds_used = round_number
        revised, errors = parse_csv(response.text, spec.outputs)
        if not revised:
            break  # unusable answer: keep the previous test set
        tests, format_errors = revised, errors
    return tests, format_errors, calls, rounds_used

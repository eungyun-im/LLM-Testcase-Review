"""Feedback refinement (FR): repair a test set with automatic check results.

Starts from an existing test set (the B1 output of the same repetition).

extend() is the procedure the experiment evaluates. It separates the two
things a test consists of:

  inputs            The model adds test cases for the gaps the checks found,
                    for up to MAX_ROUNDS rounds. It never rewrites a test.
  expected results  Decided once, at the end, for the whole set: the grounded
                    cross-check votes, and the majority is applied directly.

refine() is the earlier procedure, kept as a comparison condition: every
round the model receives all findings, disputed results included, and
returns the whole test set again. Two pilots showed its weakness. The
cross-check could be right about a result, and the rewrite would still bring
the mistake back, there or in another row.
"""

from dataclasses import replace

from tcgen.checks import (
    boundary_check, cross_check, formalize, mutation_check, ordered_vote, partition_check, render_feedback,
)
from tcgen.generate import load_prompt
from tcgen.schema import parse_csv, to_csv

MAX_ROUNDS = 3
# "cross" is the grounded cross-check. "cross-self" is the earlier form, in which the
# model recomputes from the raw input values. It is kept as a comparison condition.
ALL_CHECKS = frozenset({"boundary", "partition", "cross", "mutation"})


def refine(llm, spec, tests, feedback_mutants, code_under_test, enabled=ALL_CHECKS, max_rounds=MAX_ROUNDS):
    """Return (tests, format_errors, calls, rounds_used)."""
    calls, format_errors, rounds_used = [], 0, 0
    for round_number in range(1, max_rounds + 1):
        missing = boundary_check(tests, spec) if "boundary" in enabled else []
        classes = partition_check(tests, spec) if "partition" in enabled else []
        flagged, facts = {}, None
        if "cross" in enabled or "cross-self" in enabled:
            grounded = "cross" in enabled
            flagged, vote_calls = cross_check(tests, llm, spec, grounded=grounded)
            calls += [dict(call, round=round_number) for call in vote_calls]
            if grounded:
                facts = {t.tc_id: spec.fact_text(t) for t in tests if t.tc_id in flagged}
        survivors = (
            mutation_check(tests, feedback_mutants, code_under_test) if "mutation" in enabled else []
        )
        feedback = render_feedback(missing, flagged, survivors, classes, facts)
        if not feedback:
            break
        prompt = load_prompt("feedback").format(
            requirements=spec.requirement_text(),
            inputs=spec.input_text(),
            outputs=", ".join(spec.outputs),
            tests=to_csv(tests),
            feedback=feedback,
        )
        meta = {
            "tests": tests, "missing": missing, "flagged": flagged, "survivors": survivors,
            "classes": classes,
        }
        response = llm.complete(prompt, kind="feedback", meta=meta)
        calls.append({"round": round_number, "kind": "feedback", "prompt": prompt, "response": response})
        rounds_used = round_number
        revised, errors = parse_csv(response.text, spec.outputs)
        if not revised:
            break  # unusable answer: keep the previous test set
        tests, format_errors = revised, errors
    return tests, format_errors, calls, rounds_used


def _key(test):
    return test.inputs


def extend(llm, spec, tests, feedback_mutants, code_under_test, enabled=ALL_CHECKS, max_rounds=MAX_ROUNDS):
    """Additive refinement. Return (tests, format_errors, calls, rounds_used)."""
    tests = list(tests)
    calls, format_errors, rounds_used = [], 0, 0
    for round_number in range(1, max_rounds + 1):
        missing = boundary_check(tests, spec) if "boundary" in enabled else []
        classes = partition_check(tests, spec) if "partition" in enabled else []
        survivors = (
            mutation_check(tests, feedback_mutants, code_under_test) if "mutation" in enabled else []
        )
        feedback = render_feedback(missing, {}, survivors, classes)
        if not feedback:
            break
        prompt = load_prompt("extend").format(
            requirements=spec.requirement_text(),
            inputs=spec.input_text(),
            outputs=", ".join(spec.outputs),
            tests=to_csv(tests, with_expected=False),
            feedback=feedback,
        )
        meta = {"tests": tests, "missing": missing, "survivors": survivors, "classes": classes}
        response = llm.complete(prompt, kind="extend", meta=meta)
        calls.append({"round": round_number, "kind": "extend", "prompt": prompt, "response": response})
        rounds_used = round_number
        added, errors = parse_csv(response.text, spec.outputs)
        format_errors += errors
        known = {_key(test) for test in tests}
        fresh = []
        for test in added:
            if _key(test) not in known:
                known.add(_key(test))
                fresh.append(replace(test, tc_id=f"R{round_number}-{len(fresh) + 1:02d}"))
        if not fresh:
            break  # nothing usable was added: another round would ask the same again
        tests += fresh

    if tests and ("cross" in enabled or "cross-self" in enabled or "cross-ordered" in enabled):
        if "cross-ordered" in enabled:
            majority, vote_calls, _ = ordered_vote(tests, llm, spec)
        else:
            majority, vote_calls = cross_check(tests, llm, spec, grounded="cross" in enabled)
        calls += [dict(call, round=rounds_used + 1) for call in vote_calls]
        tests = [replace(t, expected=majority[t.tc_id]) if t.tc_id in majority else t for t in tests]
    elif tests and "rules" in enabled:
        # The requirements are translated into a decision table once. The table, and not the
        # model, then decides the expected result of every test.
        table, rule_calls = formalize(llm, spec)
        calls += [dict(call, round=rounds_used + 1) for call in rule_calls]
        if table is not None:
            decided = [(t, table.apply(spec, t)) for t in tests]
            tests = [replace(t, expected=output) if output else t for t, output in decided]
    return tests, format_errors, calls, rounds_used

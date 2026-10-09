"""The automatic checks that produce feedback for the next round.

None of them uses the reference implementation as an oracle for expected
results. They rely on what a real project has: the structured spec, the
requirement text and the code under test.
"""

import csv
import io
from collections import Counter

from tcgen.generate import load_prompt
from tcgen.metrics import boundary_coverage, output_of
from tcgen.schema import to_csv

VOTES = 3
BATCH = 40  # tests per cross-check prompt
MAX_SURVIVORS_REPORTED = 8


def boundary_check(tests, spec):
    """Boundary points that no test input uses."""
    covered, _, points = boundary_coverage(tests, spec)
    covered_keys = {p.key for p in covered}
    return [p for p in points if p.key not in covered_keys]


def partition_check(tests, spec):
    """Input classes of the spec that no test falls into."""
    covered = {spec.partition_of(test) for test in tests}
    return [p for p in spec.partitions if p["id"] not in covered]


def _parse_votes(text):
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.replace(" ", "").lower().startswith("tc_id,")),
        None,
    )
    if start is None:
        return {}
    block = [line for line in lines[start:] if line.strip() and not line.strip().startswith("```")]
    reader = csv.DictReader(io.StringIO("\n".join(block)), skipinitialspace=True)
    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
    return {
        (row.get("tc_id") or "").strip(): (row.get("expected") or "").strip().upper()
        for row in reader
    }


def cross_check(tests, llm, spec, votes=VOTES, grounded=True):
    """Ask the model to recompute every expected result independently, several times.

    grounded: the model does not see the input values. It sees, for every
    test, the conditions of the spec already decided by a program ("speed is
    at least 30 km/h: yes"), and only has to apply the requirements to them.
    A pilot showed why: recomputing from raw values, a small model repeated
    its own comparison mistakes, and its votes were no better than the
    results they were supposed to check. Not grounded is that earlier form.

    Returns ({tc_id: majority result} for tests whose stated result disagrees
    with a majority, calls). A test with no majority is left alone.
    """
    ballots = [{} for _ in range(votes)]
    calls = []
    for start in range(0, len(tests), BATCH):
        batch = tests[start:start + BATCH]
        if grounded:
            prompt = load_prompt("cross_check_grounded").format(
                requirements=spec.requirement_text(),
                outputs=", ".join(spec.outputs),
                tests="\n".join(f"{t.tc_id}: {spec.fact_text(t)}" for t in batch),
            )
        else:
            prompt = load_prompt("cross_check").format(
                requirements=spec.requirement_text(),
                inputs=spec.input_text(),
                outputs=", ".join(spec.outputs),
                tests=to_csv(batch, with_expected=False),
            )
        for ballot in ballots:
            response = llm.complete(prompt, kind="cross_check", meta={"tests": batch})
            ballot.update(_parse_votes(response.text))
            calls.append({"kind": "cross_check", "prompt": prompt, "response": response})
    flagged = {}
    for test in tests:
        answers = [b[test.tc_id] for b in ballots if b.get(test.tc_id) in spec.outputs]
        if not answers:
            continue
        winner, count = Counter(answers).most_common(1)[0]
        if count > votes / 2 and winner != test.expected:
            flagged[test.tc_id] = winner
    return flagged, calls


def mutation_check(tests, feedback_mutants, code_under_test):
    """Feedback mutants that no test input can tell from the code under test.

    A mutant counts as killed when some test input makes it behave differently
    from the code under test. Expected results play no part, so this check
    cannot leak which tests are right.
    """
    survivors = []
    for mutant in feedback_mutants:
        mutated = mutant.load()
        killed = any(output_of(mutated, t) != output_of(code_under_test, t) for t in tests)
        if not killed:
            survivors.append(mutant)
    return survivors


def render_feedback(missing, flagged, survivors, classes=(), facts=None):
    """Feedback text for the next prompt. Empty string when nothing was found.

    classes: input classes without a test. facts: {tc_id: decided conditions},
    shown next to a disputed result so the revision starts from the same
    facts the recomputation used.
    """
    sections = []
    facts = facts or {}
    if classes:
        lines = "\n".join(f"- {p['text']}" for p in classes)
        sections.append(f"Input classes with no test:\n{lines}")
    if missing:
        lines = "\n".join(f"- {p.describe()}" for p in missing)
        sections.append(f"Boundary points with no test:\n{lines}")
    if flagged:
        lines = "\n".join(
            f"- {tc_id}{' (' + facts[tc_id] + ')' if tc_id in facts else ''}: "
            f"an independent recomputation gives {result}"
            for tc_id, result in flagged.items()
        )
        sections.append(f"Expected results that an independent recomputation disagrees with:\n{lines}")
    if survivors:
        shown = survivors[:MAX_SURVIVORS_REPORTED]
        lines = "\n".join(f"- {m.description}" for m in shown)
        more = len(survivors) - len(shown)
        if more:
            lines += f"\n- and {more} more"
        sections.append(
            "Code changes that no test would notice (each should make at least one test fail):\n"
            + lines
        )
    return "\n\n".join(sections)

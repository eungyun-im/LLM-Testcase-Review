"""The three automatic checks that produce feedback for the next round.

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
MAX_SURVIVORS_REPORTED = 8


def boundary_check(tests, spec):
    """Boundary points that no test input uses."""
    covered, _, points = boundary_coverage(tests, spec)
    covered_keys = {p.key for p in covered}
    return [p for p in points if p.key not in covered_keys]


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


def cross_check(tests, llm, spec, votes=VOTES):
    """Ask the model to recompute every expected result independently, several times.

    Returns ({tc_id: majority result} for tests whose stated result disagrees
    with a majority, calls). A test with no majority is left alone.
    """
    prompt = load_prompt("cross_check").format(
        requirements=spec.requirement_text(),
        inputs=spec.input_text(),
        outputs=", ".join(spec.outputs),
        tests=to_csv(tests, with_expected=False),
    )
    ballots, calls = [], []
    for _ in range(votes):
        response = llm.complete(prompt, kind="cross_check", meta={"tests": tests})
        ballots.append(_parse_votes(response.text))
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


def render_feedback(missing, flagged, survivors):
    """Feedback text for the next prompt. Empty string when nothing was found."""
    sections = []
    if missing:
        lines = "\n".join(f"- {p.describe()}" for p in missing)
        sections.append(f"Boundary points with no test:\n{lines}")
    if flagged:
        lines = "\n".join(
            f"- {tc_id}: an independent recomputation gives {result}" for tc_id, result in flagged.items()
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

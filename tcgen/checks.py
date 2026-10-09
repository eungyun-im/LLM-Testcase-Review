"""The automatic checks that produce feedback for the next round.

None of them uses the reference implementation as an oracle for expected
results. They rely on what a real project has: the structured spec, the
requirement text and the code under test.
"""

import csv
import io
import re
from collections import Counter
from dataclasses import dataclass

from tcgen.generate import load_prompt
from tcgen.metrics import boundary_coverage, output_of
from tcgen.schema import to_csv

VOTES = 3
RULE_VOTES = 3  # decision tables requested from the model
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


@dataclass(frozen=True)
class RuleTable:
    """Ordered decision rules over the conditions of the spec. First match wins."""

    rules: tuple  # ((("C-ID", True), ...), "OUTPUT"), the last one usually with no conditions

    def apply(self, spec, test):
        """Output the table gives for a test, or None when no rule matches."""
        facts = spec.facts(test)
        for conditions, output in self.rules:
            if all(facts[cid] == wanted for cid, wanted in conditions):
                return output
        return None


_YES, _NO = {"yes", "true", "1"}, {"no", "false", "0"}


def parse_rule_table(text, spec):
    """Read a decision table from model output. None when it cannot be used as it stands.

    Nothing is repaired: an unknown condition, a value other than yes or no, an
    output that is not defined, or a missing row makes the whole table unusable.
    """
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.replace(" ", "").lower().startswith("rule,")), None)
    if start is None:
        return None
    block = [lines[start]]
    for line in lines[start + 1:]:
        if line.strip().startswith("```"):
            break
        if line.strip():
            block.append(line)
    reader = csv.DictReader(io.StringIO("\n".join(block)), skipinitialspace=True)
    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
    known = {c["id"] for c in spec.conditions}
    rules = []
    for row in reader:
        when = (row.get("when") or "").strip()
        then = (row.get("then") or "").split("#")[0].strip().upper()
        if then not in spec.outputs:
            return None
        conditions = []
        if when.lower() not in ("", "otherwise", "else", "always"):
            for part in when.split(";"):
                name, _, value = part.partition("=")
                name, value = name.strip().upper(), value.strip().lower()
                if name not in known or value not in _YES | _NO:
                    return None
                conditions.append((name, value in _YES))
        rules.append((tuple(conditions), then))
    return RuleTable(tuple(rules)) if rules else None


def formalize(llm, spec, votes=RULE_VOTES):
    """Ask the model, once per vote, for the decision rules of the requirements.

    The requirements are translated into a table once, instead of being
    applied again for every test. The most common table is used.
    Returns (RuleTable or None, calls).
    """
    prompt = load_prompt("formalize").format(
        requirements=spec.requirement_text(),
        conditions=spec.condition_table_text(),
        outputs=", ".join(spec.outputs),
    )
    tables, calls = [], []
    for _ in range(votes):
        response = llm.complete(prompt, kind="formalize", meta={})
        calls.append({"kind": "formalize", "prompt": prompt, "response": response})
        table = parse_rule_table(response.text, spec)
        if table is not None:
            tables.append(table)
    if not tables:
        return None, calls
    winner, _ = Counter(table.rules for table in tables).most_common(1)[0]
    return next(table for table in tables if table.rules == winner), calls


def last_output(text, outputs):
    """The last defined output named in a short answer, or None."""
    found = re.findall("|".join(map(re.escape, outputs)), text.upper().replace(" ", "_"))
    return found[-1] if found else None


def votes_in(prompt, response_text, outputs):
    """{tc_id: answer} from one stored cross-check call, whichever way it was asked."""
    votes = _parse_votes(response_text)
    if votes:
        return votes
    match = re.search(r"Case (\S+):", prompt)
    answer = last_output(response_text, outputs)
    return {match.group(1): answer} if match and answer else {}


def ordered_vote(tests, llm, spec, votes=VOTES):
    """The grounded vote, asked about one test at a time with the order of the requirements given.

    One question per test and vote, so a long list does not blur the answers, and
    the model is told in which order to go through the requirements instead of
    having to find it in the notes. Like the other forms, it sees the decided
    conditions and never the input values or the stated result.

    Returns ({tc_id: majority} for tests whose stated result disagrees with a
    majority, calls, {tc_id: answer} for tests on which every vote agrees).
    """
    template = load_prompt("cross_check_ordered")
    ballots = {test.tc_id: [] for test in tests}
    calls = []
    for test in tests:
        prompt = template.format(
            requirements=spec.requirement_text(),
            outputs=", ".join(spec.outputs),
            tc_id=test.tc_id,
            facts=spec.fact_text(test),
            order=spec.order_text(),
        )
        for _ in range(votes):
            response = llm.complete(prompt, kind="cross_check", meta={"tests": [test]})
            calls.append({"kind": "cross_check", "prompt": prompt, "response": response})
            answer = last_output(response.text, spec.outputs)
            if answer:
                ballots[test.tc_id].append(answer)
    flagged, unanimous = {}, {}
    for test in tests:
        answers = ballots[test.tc_id]
        if not answers:
            continue
        winner, count = Counter(answers).most_common(1)[0]
        if count > votes / 2 and winner != test.expected:
            flagged[test.tc_id] = winner
        if count == votes:
            unanimous[test.tc_id] = winner
    return flagged, calls, unanimous


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

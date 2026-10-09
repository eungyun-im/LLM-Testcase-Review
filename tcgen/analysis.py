"""Error analysis of stored runs: where the expected results go wrong, and
how well the cross-check points at the wrong ones.

    python -m tcgen.analysis --db results/pilot/qwen2.5-7b.db

Everything is recomputed from the stored prompts, answers and tests. Nothing
is run against a model.
"""

import argparse
from collections import Counter, defaultdict

from sut.aeb import decide as reference
from tcgen import store
from tcgen.checks import VOTES, _parse_votes
from tcgen.metrics import output_of
from tcgen.schema import TestCase, parse_csv
from tcgen.spec import ROOT, load_spec

GROUNDED_MARKER = "already been decided"


def final_tests(conn, condition):
    rows = conn.execute(
        "SELECT t.* FROM tests AS t JOIN runs AS r ON r.id = t.run_id WHERE r.condition = ?",
        (condition,),
    )
    return [
        TestCase(row["tc_id"], row["req_id"], row["speed_kph"], row["obstacle_m"],
                 row["sensor_age_ms"], row["expected"])
        for row in rows
    ]


def errors_by_class(tests, spec):
    """{input class: (tests, wrong, most common wrong answer)}"""
    counts = defaultdict(lambda: [0, 0, Counter()])
    for test in tests:
        entry = counts[spec.partition_of(test)]
        entry[0] += 1
        truth = output_of(reference, test)
        if test.expected != truth:
            entry[1] += 1
            entry[2][f"{test.expected} instead of {truth}"] += 1
    return {
        name: (total, wrong, mistakes.most_common(1)[0][0] if mistakes else "")
        for name, (total, wrong, mistakes) in counts.items()
    }


def cross_check_rounds(conn, outputs):
    """Yield (form, tests with their stated results, ballots) for every round that ran the cross-check.

    The test set a round voted on is not stored separately. It is recovered
    from the feedback prompt of the same round, which lists it in full.
    """
    rounds = defaultdict(lambda: {"ballots": [], "tests": None, "form": "ungrounded"})
    for row in conn.execute("SELECT run_id, round, kind, prompt, response FROM llm_calls ORDER BY id"):
        entry = rounds[(row["run_id"], row["round"])]
        if row["kind"] == "cross_check":
            entry["ballots"].append(_parse_votes(row["response"]))
            if GROUNDED_MARKER in row["prompt"]:
                entry["form"] = "grounded"
        elif row["kind"] == "feedback":
            listing = row["prompt"].split("Current test cases:", 1)[-1].split("Findings:", 1)[0]
            entry["tests"] = parse_csv(listing, outputs)[0]
    for entry in rounds.values():
        if entry["tests"] and len(entry["ballots"]) == VOTES:
            yield entry["form"], entry["tests"], entry["ballots"]


def triage(conn, outputs, form):
    """How one form of the cross-check performs as a detector of wrong expected results."""
    tally = Counter()
    for found, tests, ballots in cross_check_rounds(conn, outputs):
        if found != form:
            continue
        for test in tests:
            truth = output_of(reference, test)
            answers = [b[test.tc_id] for b in ballots if b.get(test.tc_id) in outputs]
            wrong = test.expected != truth
            tally["tests"] += 1
            tally["wrong"] += wrong
            for answer in answers:
                tally["votes"] += 1
                tally["votes right"] += answer == truth
            if not answers:
                tally["no vote"] += 1
                continue
            winner, count = Counter(answers).most_common(1)[0]
            majority = count > VOTES / 2
            tally["unanimous"] += len(set(answers)) == 1 and len(answers) == VOTES
            flagged = majority and winner != test.expected
            tally["flagged"] += flagged
            tally["flagged and wrong"] += flagged and wrong
            tally["flagged, majority right"] += flagged and winner == truth
            # A stricter rule: keep a test only when all votes agree with it.
            confirmed = len(answers) == VOTES and set(answers) == {test.expected}
            tally["confirmed"] += confirmed
            tally["confirmed and right"] += confirmed and not wrong
    return tally


def ratio(part, whole):
    return f"{part / whole:.0%} ({part} of {whole})" if whole else "n/a"


def render(conn):
    spec = load_spec()
    outputs = spec.outputs
    parts = ["# Error analysis", ""]

    parts += ["## Where the expected results are wrong", "",
              "Final test sets of all repetitions, by input class.", ""]
    for condition in ("B0", "B1", "FR", "FR-self"):
        tests = final_tests(conn, condition)
        if not tests:
            continue
        table = errors_by_class(tests, spec)
        parts += [f"**{condition}** ({len(tests)} tests)", "",
                  "| Input class | Tests | Share of all tests | Wrong | Most common mistake |",
                  "|---|---|---|---|---|"]
        for partition in spec.partitions:
            total, wrong, mistake = table.get(partition["id"], (0, 0, ""))
            parts.append(
                f"| {partition['text']} | {total} | {total / len(tests):.0%} | {ratio(wrong, total)} | {mistake} |"
            )
        parts.append("")

    for form in ("ungrounded", "grounded"):
        tally = triage(conn, outputs, form)
        if not tally["tests"]:
            continue
        parts += [
            f"## The {form} cross-check as a detector of wrong expected results", "",
            f"Every round that ran it: {tally['tests']} test results voted on, {VOTES} votes each.", "",
            "| Question | Answer |", "|---|---|",
            f"| Stated expected results that were wrong | {ratio(tally['wrong'], tally['tests'])} |",
            f"| Single votes that were right | {ratio(tally['votes right'], tally['votes'])} |",
            f"| Wrong results that were flagged (recall) | {ratio(tally['flagged and wrong'], tally['wrong'])} |",
            f"| Flagged results that were really wrong (precision) | {ratio(tally['flagged and wrong'], tally['flagged'])} |",
            f"| Flags whose proposed result was the right one | {ratio(tally['flagged, majority right'], tally['flagged'])} |",
            f"| Results confirmed by all {VOTES} votes | {ratio(tally['confirmed'], tally['tests'])} |",
            f"| Confirmed results that were right | {ratio(tally['confirmed and right'], tally['confirmed'])} |",
            "",
        ]
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Error analysis of stored runs.")
    parser.add_argument("--db", default=str(ROOT / "data" / "results.db"))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    conn = store.connect(args.db)
    text = render(conn)
    conn.close()
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)


if __name__ == "__main__":
    main()

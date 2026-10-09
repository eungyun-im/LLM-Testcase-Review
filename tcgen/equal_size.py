"""Detection at equal test counts: is a test set better, or only bigger?

    python -m tcgen.equal_size --db results/confirm/qwen2.5-7b.db

A condition that produces more tests has more chances to hit a defect. Here
every test set of a repetition is cut down to the size of the smallest one in
that repetition, by drawing random subsets, and detection is measured on the
subsets. Everything is recomputed from the stored tests.
"""

import argparse
import random
from statistics import mean

from tcgen import metrics, store
from tcgen.experiment import make_context
from tcgen.report import LABELS, ORDER
from tcgen.schema import TestCase
from tcgen.spec import ROOT

DRAWS = 100
BASELINE = "B0"  # compared separately: it is much smaller than the others by design


def tests_by_run(conn):
    """{repetition: {condition: [tests]}} for runs that did not fail."""
    result = {}
    rows = conn.execute(
        "SELECT r.repetition, r.condition, t.* FROM runs AS r JOIN tests AS t ON t.run_id = r.id"
        " WHERE r.failure IS NULL ORDER BY r.id"
    )
    for row in rows:
        test = TestCase(row["tc_id"], row["req_id"], row["speed_kph"], row["obstacle_m"],
                        row["sensor_age_ms"], row["expected"])
        result.setdefault(row["repetition"], {}).setdefault(row["condition"], []).append(test)
    return result


def detection_of(tests, context):
    valid, _ = metrics.split_valid(tests, context.reference)
    seeded, _ = metrics.detection(valid, context.seeded)
    mutants, _ = metrics.detection(valid, context.eval_mutants, context.excluded)
    return seeded, mutants


def equal_size(conn, context, draws=DRAWS, seed=0):
    """{condition: {"size", "seeded", "mutants", "full_seeded", "full_mutants"}}, means over repetitions."""
    rng = random.Random(seed)
    collected = {}
    for conditions in tests_by_run(conn).values():
        compared = {name: tests for name, tests in conditions.items() if name != BASELINE and tests}
        if len(compared) < 2:
            continue
        size = min(len(tests) for tests in compared.values())
        for name, tests in compared.items():
            samples = [detection_of(rng.sample(tests, size), context) for _ in range(draws)]
            full = detection_of(tests, context)
            entry = collected.setdefault(name, {"size": [], "seeded": [], "mutants": [], "full_seeded": [], "full_mutants": [], "count": []})
            entry["size"].append(size)
            entry["count"].append(len(tests))
            entry["seeded"].append(mean(s for s, _ in samples))
            entry["mutants"].append(mean(m for _, m in samples))
            entry["full_seeded"].append(full[0])
            entry["full_mutants"].append(full[1])
    return {name: {key: mean(values) for key, values in entry.items()} for name, entry in collected.items()}


def render(conn):
    table = equal_size(conn, make_context())
    lines = [
        "# Detection at equal test counts",
        "",
        f"Every test set is cut to the size of the smallest set of its repetition ({DRAWS} random subsets each). "
        "Means over repetitions. B0 is left out: it is smaller by design.",
        "",
        "| Condition | Tests, full set | Tests used | Detection: seeded, full | at equal size | Detection: mutants, full | at equal size |",
        "|---|---|---|---|---|---|---|",
    ]
    for name in ORDER:
        if name in table:
            e = table[name]
            lines.append(
                f"| {LABELS[name]} | {e['count']:.1f} | {e['size']:.1f} | {e['full_seeded']:.0%} | {e['seeded']:.0%} "
                f"| {e['full_mutants']:.0%} | {e['mutants']:.0%} |"
            )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Detection at equal test counts.")
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

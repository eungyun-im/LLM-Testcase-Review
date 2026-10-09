"""Result tables from the stored runs.

    python -m tcgen.report --db data/results.db
"""

import argparse

from sut.defects import SEEDED
from tcgen import stats, store
from tcgen.spec import ROOT

ORDER = ["B0", "B1", "FR", "FR-boundary", "FR-cross", "FR-mutation", "H"]
LABELS = {
    "B0": "B0 single shot",
    "B1": "B1 enhanced prompt",
    "FR": "FR feedback refinement",
    "FR-boundary": "FR without boundary feedback",
    "FR-cross": "FR without cross-check",
    "FR-mutation": "FR without mutation feedback",
    "H": "H human design",
}
COMPARISONS = [
    # (first, second, paired)
    ("B0", "B1", False),
    ("FR", "B1", True),
    ("FR", "FR-boundary", True),
    ("FR", "FR-cross", True),
    ("FR", "FR-mutation", True),
]
MAIN_METRICS = ["error_rate", "detection_seeded", "detection_mutants"]
SIMULATED_WARNING = (
    "> **Simulated data.** These runs used the built-in simulator, not a real model. "
    "They show that the pipeline works and nothing else."
)


def _cell(values, percent=True):
    mean, sd = stats.mean_sd(values)
    if mean is None:
        return ""
    if len(values) == 1:
        return f"{mean:.0%}" if percent else f"{mean:.1f}"
    return f"{mean:.0%} ± {sd:.0%}" if percent else f"{mean:.1f} ± {sd:.1f}"


def _systems(conn):
    return [row["system"] for row in conn.execute("SELECT DISTINCT system FROM runs ORDER BY system")]


def uses_simulator(conn):
    return conn.execute("SELECT 1 FROM runs WHERE client = 'simulated' LIMIT 1").fetchone() is not None


def models_line(conn):
    """Which model produced the runs: a result means nothing without it."""
    rows = conn.execute(
        "SELECT client, model, COUNT(*) AS runs, MIN(started_at) AS first, MAX(started_at) AS last"
        " FROM runs WHERE client != 'human' GROUP BY client, model ORDER BY client, model"
    ).fetchall()
    return "\n".join(
        f"- `{row['model']}` through the {row['client']} client: {row['runs']} runs, "
        f"{row['first'][:10]} to {row['last'][:10]}"
        for row in rows
    )


def table_summary(conn, system):
    lines = [
        "| Condition | Runs | Tests | Rows rejected | Error rate | Boundary recall (simple / strict) | Detection: seeded | Detection: mutants | LLM calls |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for condition in ORDER:
        values = {
            name: list(store.metric_values(conn, system, condition, name).values())
            for name in (
                "generated", "format_errors", "error_rate", "boundary_recall_simple", "boundary_recall_strict",
                "detection_seeded", "detection_mutants", "llm_calls",
            )
        }
        if not values["generated"]:
            continue
        recall = f"{_cell(values['boundary_recall_simple'])} / {_cell(values['boundary_recall_strict'])}"
        calls = "" if condition == "H" else _cell(values["llm_calls"], percent=False)
        lines.append(
            f"| {LABELS[condition]} | {len(values['generated'])} | {_cell(values['generated'], percent=False)} | "
            f"{_cell(values['format_errors'], percent=False)} | "
            f"{_cell(values['error_rate'])} | {recall} | {_cell(values['detection_seeded'])} | "
            f"{_cell(values['detection_mutants'])} | {calls} |"
        )
    return "\n".join(lines)


def table_seeded(conn, system):
    conditions = ["B0", "B1", "FR", "H"]
    lines = ["| Defect | Type | " + " | ".join(conditions) + " |", "|---|---|" + "---|" * len(conditions)]
    for defect_id, (kind, _, _) in SEEDED.items():
        cells = []
        for condition in conditions:
            row = conn.execute(
                "SELECT COALESCE(SUM(d.detected), 0) AS found, COUNT(*) AS total"
                " FROM detections AS d JOIN runs AS r ON r.id = d.run_id"
                " WHERE r.system = ? AND r.condition = ? AND d.defect_set = 'seeded' AND d.defect_id = ?",
                (system, condition, defect_id),
            ).fetchone()
            cells.append(f"{row['found']}/{row['total']}" if row["total"] else "")
        lines.append(f"| {defect_id} | {kind} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def table_comparisons(conn, system):
    results = []
    for first, second, paired in COMPARISONS:
        for metric in MAIN_METRICS:
            outcome = stats.compare(conn, system, metric, first, second, paired)
            if outcome:
                results.append((f"{first} vs {second}: {metric}", paired, outcome))
    if not results:
        return ""
    adjusted = stats.holm({name: outcome["p"] for name, _, outcome in results})
    lines = [
        "| Comparison | Test | Means | A12 | p | p (Holm) |",
        "|---|---|---|---|---|---|",
    ]
    for name, paired, outcome in results:
        test = "Wilcoxon" if paired else "Mann-Whitney"
        means = f"{outcome['mean_first']:.0%} vs {outcome['mean_second']:.0%}"
        lines.append(
            f"| {name} | {test} | {means} | {outcome['a12']:.2f} | {outcome['p']:.3f} | {adjusted[name]:.3f} |"
        )
    return "\n".join(lines)


def render(conn):
    parts = ["# Results", ""]
    if uses_simulator(conn):
        parts += [SIMULATED_WARNING, ""]
    parts += [models_line(conn), ""]
    for system in _systems(conn):
        parts += [f"## {system}", "", "### Table 1. Metrics by condition", "", table_summary(conn, system), ""]
        parts += ["### Table 2. Seeded defects detected (runs that detected / runs)", "", table_seeded(conn, system), ""]
        comparisons = table_comparisons(conn, system)
        if comparisons:
            parts += ["### Table 3. Statistical comparisons", "", comparisons, ""]
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Render result tables from stored runs.")
    parser.add_argument("--db", default=str(ROOT / "data" / "results.db"))
    parser.add_argument("--out", default=None, help="write the report to this file as well")
    args = parser.parse_args()
    conn = store.connect(args.db)
    text = render(conn)
    conn.close()
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    main()

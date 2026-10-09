"""Figures from stored runs of a real model.

    python -m tools.result_figures results/confirm/qwen2.5-7b.db results/confirm/qwen2.5-3b.db

Writes docs/img/error-rate-<model>-{light,dark}.svg: the error rate of every
repetition, by condition, with the mean. One figure per database.
"""

import sys
from statistics import mean

from tcgen import store
from tcgen.spec import ROOT
from tools.svgfig import Figure, save_both, scale

IMG = ROOT / "docs" / "img"

# condition: (label, what it is)
ROWS = [
    ("B1", "B1, the starting set", "one generation with the structured spec"),
    ("FR-cross", "Extended, results as written", "the model adds tests, nobody checks the results"),
    ("FR-self", "Extended, ungrounded vote", "the model recomputes from the raw values"),
    ("FR-rewrite", "Rewrite loop, grounded findings", "the model returns the whole set every round"),
    ("FR", "Extended, grounded vote", "the proposed method"),
]


def error_rates(conn, condition):
    values = store.metric_values(conn, _system(conn), condition, "error_rate")
    return [values[key] for key in sorted(values)]


def _system(conn):
    return conn.execute("SELECT system FROM runs LIMIT 1").fetchone()["system"]


def _model(conn):
    return conn.execute("SELECT model FROM runs WHERE client != 'human' LIMIT 1").fetchone()["model"]


def error_rate_figure(mode, conn):
    model = _model(conn)
    data = [(label, note, error_rates(conn, condition), condition) for condition, label, note in ROWS]
    data = [row for row in data if row[2]]
    repetitions = max(len(row[2]) for row in data)
    row_h = 46
    fig = Figure(
        760, 92 + row_h * len(data) + 46, mode,
        f"Share of wrong expected results, {model}, {repetitions} repetitions",
        "One dot per repetition, the bar marks the mean. Lower is better",
    )
    label_x, left, right, top = 24, 300, 690, 84
    x = scale((0, 1), (left, right))
    for tick in (0, 0.25, 0.5, 0.75, 1):
        fig.line(x(tick), top - 6, x(tick), top + row_h * len(data) - 8)
        fig.text(x(tick), top + row_h * len(data) + 10, f"{tick:.0%}", size=11, color="secondary", anchor="middle")
    for index, (label, note, values, condition) in enumerate(data):
        y = top + index * row_h + 14
        role = "series1" if condition == "FR" else "secondary"
        fig.text(label_x, y - 2, label, size=13, weight=700 if condition == "FR" else 600)
        fig.text(label_x, y + 14, note, size=10, color="secondary")
        for value in values:
            fig.add(
                f'<circle cx="{x(value):.1f}" cy="{y}" r="5" fill="{fig.color(role)}" fill-opacity="0.55" '
                f'stroke="{fig.color("surface")}" stroke-width="1"/>'
            )
        average = mean(values)
        fig.line(x(average), y - 12, x(average), y + 12, stroke=role, width=3)
        fig.text(right + 14, y + 4, f"{average:.0%}", size=12, weight=700 if condition == "FR" else 400)
    legend_y = top + row_h * len(data) + 32
    fig.text(label_x, legend_y, "The four rows below B1 all start from that B1 set, in each repetition.", size=11, color="secondary")
    return fig, model


def main():
    for path in sys.argv[1:]:
        conn = store.connect(path)
        model = _model(conn).replace(":", "-")
        save_both(IMG, f"error-rate-{model}", lambda mode: error_rate_figure(mode, conn)[0])
        conn.close()


if __name__ == "__main__":
    main()

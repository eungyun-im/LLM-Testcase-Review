"""Generate the README figures from the experiment setup (not from results).

    python -m tools.figures

Writes docs/img/*.svg in a light and a dark variant. Both figures describe
inputs to the experiment: the mutant sets and the boundary points. They
contain no measurement of any model.
"""

from tcgen import mutation
from tcgen.spec import ROOT, load_spec
from tools.svgfig import Figure, save_both

IMG = ROOT / "docs" / "img"
KIND_LABELS = {
    "constant": ("Constant", "30.0 becomes 31.0"),
    "return": ("Return value", "BRAKE becomes NO_ACTION"),
    "relational": ("Comparison", ">= becomes >"),
    "logical": ("Logic", "and becomes or"),
}


def mutant_split_figure(mode):
    mutants = mutation.generate()
    feedback, evaluation = mutation.split(mutants)
    kinds = sorted(KIND_LABELS, key=lambda k: -sum(m.kind == k for m in mutants))
    fig = Figure(
        760, 354, mode,
        f"{len(mutants)} mutants, split by operator: {len(feedback)} for feedback, {len(evaluation)} held out for scoring",
        "A test set is never scored on the mutants it was shown as feedback",
    )
    label_x, bar_x, unit, thickness, gap = 24, 250, 56, 14, 2
    for row, kind in enumerate(kinds):
        y = 86 + row * 54
        title, example = KIND_LABELS[kind]
        fig.text(label_x, y + 12, title, size=13, weight=600)
        fig.text(label_x, y + 28, example, size=11, color="secondary")
        for offset, (group, role) in enumerate(((feedback, "series1"), (evaluation, "series2"))):
            count = sum(m.kind == kind for m in group)
            top = y + offset * (thickness + gap)
            if count:
                fig.bar(bar_x, top, count * unit, thickness, role)
            fig.text(bar_x + count * unit + 10, top + 11, count, size=11, color="secondary")
    legend_y = 86 + len(kinds) * 54 + 12
    for line, role, label in (
        (0, "series1", "Feedback set: shown to the model as surviving mutants"),
        (1, "series2", "Evaluation set: used only for the detection rate"),
    ):
        fig.rect(label_x, legend_y - 9 + 20 * line, 12, 12, role, rx=2)
        fig.text(label_x + 18, legend_y + 1 + 20 * line, label, size=11, color="secondary")
    return fig


def boundary_points_figure(mode):
    spec = load_spec()
    points = spec.points()
    fig = Figure(
        760, 96 + 46 * len(spec.boundaries) + 16, mode,
        f"Boundary recall counts {len(points)} points: three per threshold in the spec",
        "A generated test set is checked for each value: one resolution step below, at, and above the boundary",
    )
    label_x, columns, top = 24, (330, 480, 630), 104
    for heading, x in zip(("just below", "at the boundary", "just above"), columns):
        fig.text(x, top - 20, heading, size=12, color="secondary", anchor="middle")
    fig.line(label_x, top - 6, 736, top - 6)
    for index, boundary in enumerate(spec.boundaries):
        y = top + 22 + index * 46
        unit = spec.inputs[boundary["input"]]["unit"]
        fig.text(label_x, y + 1, boundary["id"], size=13, weight=600)
        fig.text(label_x, y + 17, f"{boundary['input']} = {boundary['value']:g} {unit}", size=11, color="secondary")
        row = [p for p in points if p.boundary_id == boundary["id"]]
        for point, x in zip(row, columns):
            fig.dot(x - 26, y + 4, "series1", r=5)
            fig.text(x - 14, y + 8, f"{point.value:g}", size=12, weight=600)
        fig.line(label_x, y + 28, 736, y + 28)
    return fig


def main():
    save_both(IMG, "mutant-split", mutant_split_figure)
    save_both(IMG, "boundary-points", boundary_points_figure)


if __name__ == "__main__":
    main()

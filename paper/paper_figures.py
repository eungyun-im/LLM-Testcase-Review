"""Figures of the paper, one column wide (7.5 cm), readable in black and white.

    python paper/paper_figures.py

Reads paper/numbers.json (paper_numbers.py) and writes paper/fig1.png, fig2.png, fig3.png at 300 dpi.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

HERE = Path(__file__).resolve().parent
WIDTH_IN = 2.95  # 7.5 cm, one column of the template
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 6, "axes.linewidth": 0.5, "xtick.major.width": 0.5,
    "ytick.major.width": 0.5, "savefig.dpi": 300,
})
INK, GRAY, LIGHT = "#111111", "#6e6e6e", "#e6e6e6"


def figure_one():
    """The method as a flow: who does each step."""
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 3.55))
    ax.set_xlim(0, 10)
    ax.set_ylim(-1.9, 12.6)
    ax.axis("off")
    steps = [
        ("Requirements + structured spec", "6 conditions, 7 input classes,\norder of the requirements", "spec"),
        ("LLM writes the first test set (B1)", "test inputs and expected results", "llm"),
        ("Checks find gaps; LLM adds tests only", "boundary points, input classes,\nsurviving mutants (up to 3 rounds)", "llm"),
        ("Program decides the conditions", "\"speed >= 30 km/h: yes\", for every test", "program"),
        ("LLM votes three times, one test per query", "facts + requirements in the given order", "llm"),
        ("Majority vote = expected result", "no reference implementation involved", "program"),
    ]
    top, height, gap = 12.2, 1.55, 0.72
    for index, (title, detail, kind) in enumerate(steps):
        y = top - index * (height + gap)
        face = LIGHT if kind == "llm" else "white"
        style = dict(boxstyle="round,pad=0.02,rounding_size=0.25", linewidth=0.7, edgecolor=INK, facecolor=face)
        if kind == "spec":
            style["linewidth"] = 1.3
        ax.add_patch(FancyBboxPatch((0.4, y - height), 9.2, height, **style))
        ax.text(5, y - 0.42, title, ha="center", va="center", fontsize=6.4, fontweight="bold", color=INK)
        ax.text(5, y - 1.08, detail, ha="center", va="center", fontsize=5.6, color=INK, linespacing=1.15)
        if index < len(steps) - 1:
            ax.annotate("", xy=(5, y - height - gap + 0.04), xytext=(5, y - height - 0.02),
                        arrowprops=dict(arrowstyle="-|>", lw=0.7, color=INK, mutation_scale=6))
    ax.add_patch(FancyBboxPatch((0.4, -1.55), 0.9, 0.5, boxstyle="round,pad=0.01", facecolor=LIGHT, edgecolor=INK, lw=0.5))
    ax.text(1.55, -1.3, "LLM call", fontsize=5.4, va="center")
    ax.add_patch(FancyBboxPatch((4.0, -1.55), 0.9, 0.5, boxstyle="round,pad=0.01", facecolor="white", edgecolor=INK, lw=0.5))
    ax.text(5.15, -1.3, "program", fontsize=5.4, va="center")
    ax.add_patch(FancyBboxPatch((7.2, -1.55), 0.9, 0.5, boxstyle="round,pad=0.01", facecolor="white", edgecolor=INK, lw=1.3))
    ax.text(8.25, -1.3, "spec", fontsize=5.4, va="center")
    fig.savefig(HERE / "fig1.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


ROWS = [
    ("B1", "Start: B1"),
    ("FR-cross", "Extended, results as written"),
    ("FR-self", "Vote on raw values"),
    ("FR-rewrite", "Model rewrites the set"),
    ("FR", "Grounded vote, 40 per query"),
    ("FR-ordered", "Proposed: ordered, 1 per query"),
]


def figure_two(model):
    """Error rate of every repetition, by condition, for one model."""
    rows = [(key, label) for key, label in ROWS if key in model["conditions"] and model["conditions"][key]["error_rate"]["n"]]
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 0.36 * len(rows) + 0.55))
    for index, (key, label) in enumerate(rows):
        y = len(rows) - 1 - index
        values = model["conditions"][key]["error_rate"]["values"]
        proposed = key == "FR-ordered"
        for j, value in enumerate(values):
            jitter = ((j % 5) - 2) * 0.055
            ax.plot(value * 100, y + jitter, marker="o" if proposed else "s", markersize=2.6,
                    markerfacecolor=INK if proposed else "white", markeredgecolor=INK, markeredgewidth=0.5, linestyle="none")
        mean = sum(values) / len(values) * 100
        ax.plot([mean, mean], [y - 0.3, y + 0.3], color=INK, lw=1.4)
        ax.text(101.5, y, f"{mean:.0f}%", va="center", fontsize=6, fontweight="bold" if proposed else "normal")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([label for _, label in rows][::-1], fontsize=5.8)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("Share of wrong expected results (%)", fontsize=6)
    ax.tick_params(axis="both", labelsize=5.8, length=2)
    ax.grid(axis="x", color=LIGHT, lw=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.savefig(HERE / "fig2.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def figure_three(models):
    """How often a single vote is right, by model and form of the vote."""
    forms = [("FR-self", "Raw values", "white", ""), ("FR", "Grounded,\n40 per query", LIGHT, "//"),
             ("FR-ordered", "Grounded, ordered,\n1 per query", INK, "")]
    models = [m for m in models if any(f in m["votes"] for f, *_ in forms)]
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 1.9))
    width = 0.26
    for j, (key, label, face, hatch) in enumerate(forms):
        xs, heights = [], []
        for i, m in enumerate(models):
            if key in m["votes"] and m["votes"][key]["single_right"] is not None:
                xs.append(i + (j - 1) * width)
                heights.append(m["votes"][key]["single_right"] * 100)
        bars = ax.bar(xs, heights, width * 0.92, label=label, facecolor=face, edgecolor=INK, linewidth=0.6, hatch=hatch)
        for rect, h in zip(bars, heights):
            ax.text(rect.get_x() + rect.get_width() / 2, h + 1.5, f"{h:.0f}", ha="center", fontsize=5.4)
    ax.axhline(33.3, color=GRAY, lw=0.6, ls=":")
    ax.text(-0.62, 28, "chance (1 of 3)", fontsize=5.2, color=GRAY, ha="left", va="top")
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([m["model"].replace("qwen2.5:", "Qwen2.5 ") for m in models], fontsize=6)
    ax.set_ylim(0, 112)
    ax.set_ylabel("Single vote right (%)", fontsize=6)
    ax.tick_params(axis="y", labelsize=5.8, length=2)
    ax.legend(fontsize=5.2, frameon=False, loc="upper left", ncol=3, handlelength=1.2, columnspacing=0.8, bbox_to_anchor=(-0.02, 1.16))
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.savefig(HERE / "fig3.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def main():
    numbers = json.loads((HERE / "numbers.json").read_text(encoding="utf-8"))
    models = numbers["models"]
    main_model = next((m for m in models if m["model"] == "qwen2.5:7b"), models[0])
    figure_one()
    figure_two(main_model)
    figure_three(models)
    print("wrote fig1.png fig2.png fig3.png")


if __name__ == "__main__":
    main()

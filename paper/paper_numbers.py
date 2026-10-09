"""Every number of the paper, computed from the stored runs.

    python paper/paper_numbers.py results/v2/qwen2.5-3b.db results/v2/qwen2.5-7b.db results/v2/qwen2.5-14b.db

Prints a JSON document and writes it to paper/numbers.json. Nothing in the text
of the paper is typed in by hand: the text is a template that reads this file.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tcgen import stats, store  # noqa: E402
from tcgen.analysis import final_votes  # noqa: E402
from tcgen.equal_size import equal_size  # noqa: E402
from tcgen.experiment import make_context  # noqa: E402
from tcgen.spec import load_spec  # noqa: E402

CONDITIONS = ["B0", "B1", "FR", "FR-cross", "FR-self", "FR-rewrite", "FR-ordered"]
METRICS = ["generated", "format_errors", "error_rate", "detection_seeded", "detection_mutants", "llm_calls",
           "boundary_recall_simple", "partition_coverage"]
TARGET_ERROR = 0.06  # design v2, target T


def summary(values):
    values = list(values)
    mean, sd = stats.mean_sd(values)
    return {"n": len(values), "mean": mean, "sd": sd, "values": values}


def compare(conn, system, first, second):
    outcome = stats.compare(conn, system, "error_rate", first, second, True)
    if outcome is None:
        return None
    a = store.metric_values(conn, system, first, "error_rate")
    b = store.metric_values(conn, system, second, "error_rate")
    shared = sorted(set(a) & set(b))
    outcome["lower_in"] = sum(a[r] < b[r] for r in shared)
    outcome["pairs"] = len(shared)
    return outcome


def model_numbers(db, context=None):
    conn = store.connect(db)
    system = conn.execute("SELECT system FROM runs LIMIT 1").fetchone()["system"]
    model = conn.execute("SELECT model FROM runs WHERE client != 'human' LIMIT 1").fetchone()["model"]
    effort = conn.execute("SELECT effort FROM runs WHERE client != 'human' LIMIT 1").fetchone()["effort"]
    out = {"db": str(db), "model": model, "settings": effort, "conditions": {}, "present": []}
    for condition in CONDITIONS:
        total = conn.execute("SELECT COUNT(*) FROM runs WHERE condition = ?", (condition,)).fetchone()[0]
        if not total:
            continue
        failed = conn.execute(
            "SELECT COUNT(*) FROM runs WHERE condition = ? AND failure IS NOT NULL", (condition,)).fetchone()[0]
        row = {"runs": total, "failed": failed}
        for metric in METRICS:
            row[metric] = summary(store.metric_values(conn, system, condition, metric).values())
        out["conditions"][condition] = row
        out["present"].append(condition)

    pairs = {
        "H1": ("FR-ordered", "FR"),
        "H2": ("FR-ordered", "B1"),
        "FR_B1": ("FR", "B1"),
        "ordered_self": ("FR-ordered", "FR-self"),
        "ordered_cross": ("FR-ordered", "FR-cross"),
        "ordered_rewrite": ("FR-ordered", "FR-rewrite"),
    }
    out["comparisons"] = {}
    for key, (first, second) in pairs.items():
        if first in out["present"] and second in out["present"]:
            result = compare(conn, system, first, second)
            if result:
                out["comparisons"][key] = {k: v for k, v in result.items() if k not in ("metric",)}
    primary = {k: out["comparisons"][k]["p"] for k in ("H1", "H2") if k in out["comparisons"]}
    for key, adjusted in stats.holm(primary).items():
        out["comparisons"][key]["p_holm"] = adjusted

    votes = final_votes(conn, load_spec().outputs)
    out["votes"] = {}
    for condition, t in votes.items():
        if t["tests"]:
            out["votes"][condition] = {
                "tests": t["tests"],
                "single_right": t["votes right"] / t["votes"] if t["votes"] else None,
                "majority_right": t["majority right"] / t["tests"],
                "unanimous_share": t["unanimous"] / t["tests"],
                "unanimous_right": t["unanimous right"] / t["unanimous"] if t["unanimous"] else None,
            }

    ordered = out["conditions"].get("FR-ordered")
    if ordered and ordered["error_rate"]["n"]:
        out["target"] = {"limit": TARGET_ERROR, "mean": ordered["error_rate"]["mean"],
                         "met": ordered["error_rate"]["mean"] <= TARGET_ERROR,
                         "worst": max(ordered["error_rate"]["values"])}
    if context is not None and "B1" in out["present"] and "FR-ordered" in out["present"]:
        out["equal_size"] = equal_size(conn, context)

    out["calls"] = dict(zip(("n", "input_tokens", "output_tokens", "minutes"), conn.execute(
        "SELECT COUNT(*), SUM(input_tokens), SUM(output_tokens), SUM(duration_ms)/60000.0 FROM llm_calls").fetchone()))
    out["span"] = tuple(conn.execute("SELECT MIN(started_at), MAX(started_at) FROM runs").fetchone())
    conn.close()
    return out


def main():
    context = make_context()
    result = {"models": [model_numbers(db, context) for db in sys.argv[1:]]}
    text = json.dumps(result, indent=1, default=float)
    (ROOT / "paper" / "numbers.json").write_text(text, encoding="utf-8", newline="\n")
    print(text[:6000])


if __name__ == "__main__":
    main()

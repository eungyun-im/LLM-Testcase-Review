"""Run the experiment: generate, refine, evaluate and store.

    python -m tcgen.experiment --client simulated --reps 3
    python -m tcgen.experiment --client anthropic --reps 10 --db data/results.db

Per repetition, B0 and B1 are generated once. FR and its three ablations all
start from that repetition's B1 test set, so they can be compared pairwise.
"""

import argparse
from dataclasses import dataclass

from sut.aeb import decide as reference_decide
from sut.defects import SEEDED
from tcgen import metrics, mutation, store
from tcgen.generate import generate
from tcgen.llm import AnthropicClient, DEFAULT_EFFORT, DEFAULT_MODEL, LLMError
from tcgen.refine import ALL_CHECKS, refine
from tcgen.schema import load_csv_file
from tcgen.simulator import SimulatedLLM
from tcgen.spec import ROOT, load_spec

HUMAN_BASELINE = ROOT / "data" / "human" / "aeb_baseline.csv"
FR_VARIANTS = {
    "FR": ALL_CHECKS,
    "FR-boundary": ALL_CHECKS - {"boundary"},
    "FR-cross": ALL_CHECKS - {"cross"},
    "FR-mutation": ALL_CHECKS - {"mutation"},
}
CONDITIONS = ["B0", "B1", *FR_VARIANTS]


class _Human:
    name, model, effort = "human", "human", "none"


@dataclass
class Context:
    spec: object
    reference: object
    seeded: dict
    feedback_mutants: list
    eval_mutants: dict
    excluded: set


def make_context(spec=None):
    spec = spec or load_spec()
    feedback, evaluation = mutation.split(mutation.generate())
    return Context(
        spec=spec,
        reference=reference_decide,
        seeded={defect_id: entry[2] for defect_id, entry in SEEDED.items()},
        feedback_mutants=feedback,
        eval_mutants={m.mutant_id: m.load() for m in evaluation},
        excluded=mutation.confirmed_equivalent(),
    )


def evaluate(context, tests, format_errors=0, calls=(), rounds=0):
    """Compute every metric for one test set."""
    valid, wrong = metrics.split_valid(tests, context.reference)
    simple, strict = metrics.boundary_recall(tests, context.spec)
    seeded_rate, seeded_table = metrics.detection(valid, context.seeded)
    mutant_rate, mutant_table = metrics.detection(valid, context.eval_mutants, context.excluded)
    return {
        "tests": tests,
        "valid": valid,
        "calls": list(calls),
        "rounds": rounds,
        "format_errors": format_errors,
        "detections": {"seeded": seeded_table, "mutant": mutant_table},
        "metrics": {
            "generated": len(tests),
            "format_errors": format_errors,
            "error_rate": len(wrong) / len(tests) if tests else 0.0,
            "boundary_recall_simple": simple,
            "boundary_recall_strict": strict,
            "detection_seeded": seeded_rate,
            "detection_mutants": mutant_rate,
            "llm_calls": len(calls),
            "input_tokens": sum(c["response"].input_tokens for c in calls),
            "output_tokens": sum(c["response"].output_tokens for c in calls),
            "duration_ms": sum(c["response"].duration_ms for c in calls),
        },
    }


def run_repetition(conn, llm, context, repetition, conditions=CONDITIONS):
    """Run the requested conditions for one repetition and store each."""
    system = context.spec.system

    def save(condition, result):
        store.save_run(conn, system=system, condition=condition, repetition=repetition, llm=llm, result=result)

    def attempt(condition, produce):
        try:
            result = produce()
        except LLMError as error:
            result = {"failure": str(error)}
        save(condition, result)
        return result

    if "B0" in conditions:
        attempt("B0", lambda: evaluate(context, *generate(llm, context.spec, "b0")))

    variants = [name for name in FR_VARIANTS if name in conditions]
    if "B1" not in conditions and not variants:
        return
    try:
        b1_tests, b1_errors, b1_calls = generate(llm, context.spec, "b1")
    except LLMError as error:
        for condition in ["B1", *variants]:
            save(condition, {"failure": f"B1 generation failed: {error}"})
        return
    if "B1" in conditions:
        save("B1", evaluate(context, b1_tests, b1_errors, b1_calls))

    for name in variants:
        def produce(name=name):
            tests, errors, calls, rounds = refine(
                llm, context.spec, b1_tests, context.feedback_mutants, context.reference,
                enabled=FR_VARIANTS[name],
            )
            return evaluate(context, tests, errors, [*b1_calls, *calls], rounds)

        attempt(name, produce)


def run_human_baseline(conn, context, path=HUMAN_BASELINE):
    """Evaluate the human-designed test set once, as condition H. Returns False when empty."""
    tests, errors = load_csv_file(path, context.spec.outputs)
    if not tests:
        return False
    store.save_run(
        conn, system=context.spec.system, condition="H", repetition=0, llm=_Human,
        result=evaluate(context, tests, errors),
    )
    return True


def make_client(name, context, model, effort, seed):
    if name == "anthropic":
        return AnthropicClient(model=model, effort=effort)
    return SimulatedLLM(context.spec, context.reference, seed=seed)


def main():
    parser = argparse.ArgumentParser(description="Run the test generation experiment.")
    parser.add_argument("--client", choices=["simulated", "anthropic"], default="simulated")
    parser.add_argument("--reps", type=int, default=10)
    parser.add_argument("--conditions", nargs="+", default=CONDITIONS, choices=CONDITIONS)
    parser.add_argument("--db", default=str(ROOT / "data" / "results.db"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--effort", default=DEFAULT_EFFORT)
    parser.add_argument("--seed", type=int, default=0, help="seed of the simulated client")
    parser.add_argument("--skip-human", action="store_true")
    args = parser.parse_args()

    context = make_context()
    conn = store.connect(args.db)
    llm = make_client(args.client, context, args.model, args.effort, args.seed)
    for repetition in range(1, args.reps + 1):
        run_repetition(conn, llm, context, repetition, args.conditions)
        print(f"repetition {repetition}/{args.reps} done")
    if not args.skip_human and not run_human_baseline(conn, context):
        print(f"human baseline skipped: {HUMAN_BASELINE.relative_to(ROOT)} has no test cases yet")
    conn.close()
    print(f"results stored in {args.db}")


if __name__ == "__main__":
    main()

"""Mutants of the reference implementation, split into a feedback and an evaluation set.

    python -m tcgen.mutation            # list mutants, their set and equivalence candidates

The split matters: mutants shown to the generator as feedback are never used
to score it, otherwise catching them would only prove the feedback was read.
"""

import ast
import copy
import itertools
import random
from dataclasses import dataclass
from pathlib import Path

from tcgen.spec import ROOT, load_spec

SOURCE = ROOT / "sut" / "aeb.py"
EQUIVALENT_CSV = ROOT / "data" / "mutants" / "equivalent.csv"
SPLIT_SEED = 20261008

RELATIONAL = {
    ast.GtE: ast.Gt,
    ast.Gt: ast.GtE,
    ast.LtE: ast.Lt,
    ast.Lt: ast.LtE,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Is: ast.IsNot,
    ast.IsNot: ast.Is,
}


@dataclass(frozen=True)
class Mutant:
    mutant_id: str
    kind: str
    lineno: int
    original: str
    mutated: str
    source: str

    @property
    def description(self):
        return f"line {self.lineno}: `{self.original}` changed to `{self.mutated}`"

    def load(self):
        namespace = {}
        exec(compile(self.source, f"<{self.mutant_id}>", "exec"), namespace)
        return namespace["decide"]


def _sites(tree, function_name):
    function = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function_name
    )
    used = {n.id for n in ast.walk(function) if isinstance(n, ast.Name)}
    in_scope = set(ast.walk(function))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = {n.id for t in node.targets for n in ast.walk(t) if isinstance(n, ast.Name)}
            if targets & used:
                in_scope |= set(ast.walk(node))
    return [i for i, node in enumerate(ast.walk(tree)) if node in in_scope]


def _variants(node):
    if isinstance(node, ast.Compare):
        for i, op in enumerate(node.ops):
            swap = RELATIONAL.get(type(op))
            if swap:
                yield "relational", lambda n, i=i, swap=swap: n.ops.__setitem__(i, swap())
    if isinstance(node, ast.BoolOp):
        swap = ast.Or if isinstance(node.op, ast.And) else ast.And
        yield "logical", lambda n, swap=swap: setattr(n, "op", swap())
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        for delta in (1, -1):
            yield "constant", lambda n, d=delta: setattr(n, "value", n.value + d)
    if isinstance(node, ast.Return) and isinstance(node.value, ast.Attribute):
        if isinstance(node.value.value, ast.Name) and node.value.value.id == "Action":
            for member in ("NO_ACTION", "BRAKE", "FAULT"):
                if member != node.value.attr:
                    yield "return", lambda n, m=member: setattr(n.value, "attr", m)


def generate(source_text=None, function_name="decide"):
    source_text = SOURCE.read_text(encoding="utf-8") if source_text is None else source_text
    tree = ast.parse(source_text)
    mutants = []
    for index in _sites(tree, function_name):
        node = list(ast.walk(tree))[index]
        for kind, mutate in _variants(node):
            mutated_tree = copy.deepcopy(tree)
            target = list(ast.walk(mutated_tree))[index]
            original = ast.unparse(target)
            mutate(target)
            mutants.append(
                Mutant(
                    mutant_id=f"M{len(mutants) + 1:03d}",
                    kind=kind,
                    lineno=node.lineno,
                    original=original,
                    mutated=ast.unparse(target),
                    source=ast.unparse(mutated_tree),
                )
            )
    return mutants


def split(mutants, seed=SPLIT_SEED):
    """Half for feedback, half for evaluation, balanced within each mutation kind."""
    rng = random.Random(seed)
    feedback, evaluation = [], []
    for kind in sorted({m.kind for m in mutants}):
        group = [m for m in mutants if m.kind == kind]
        rng.shuffle(group)
        for index, mutant in enumerate(group):
            (feedback if index % 2 == 0 else evaluation).append(mutant)
    by_id = lambda m: m.mutant_id
    return sorted(feedback, key=by_id), sorted(evaluation, key=by_id)


def probe_inputs(spec):
    """Dense inputs around every boundary plus a few interior values."""
    values = {name: set() for name in spec.inputs}
    for boundary in spec.boundaries:
        step = spec.inputs[boundary["input"]]["resolution"]
        for k in range(-2, 3):
            values[boundary["input"]].add(round(boundary["value"] + k * step, 6))
    values["speed_kph"] |= {15.0, 100.0}
    values["obstacle_m"] |= {0.0, 10.0, 30.0, None}
    values["sensor_age_ms"] |= {0, 50, 500}
    ordered = [sorted(values[name], key=lambda v: (v is None, v or 0)) for name in spec.inputs]
    return list(itertools.product(*ordered))


def distinguishing_input(mutant_decide, reference, probes):
    """First probe on which the mutant behaves differently, or None."""
    for probe in probes:
        try:
            # Compare by value: a mutant is loaded with its own copy of the Action enum.
            changed = mutant_decide(*probe).value != reference(*probe).value
        except Exception:
            changed = True
        if changed:
            return probe
    return None


def equivalence_candidates(mutants, reference, spec):
    """Mutants no probe can tell from the reference. A person makes the final call."""
    probes = probe_inputs(spec)
    return [m for m in mutants if distinguishing_input(m.load(), reference, probes) is None]


def confirmed_equivalent(path=EQUIVALENT_CSV):
    """Mutant IDs a person has marked equivalent in data/mutants/equivalent.csv."""
    import csv

    if not Path(path).exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {
            row["mutant_id"].strip()
            for row in csv.DictReader(f)
            if row.get("equivalent", "").strip().lower() == "yes"
        }


def main():
    from sut.aeb import decide

    spec = load_spec()
    mutants = generate()
    feedback, _ = split(mutants)
    feedback_ids = {m.mutant_id for m in feedback}
    candidates = {m.mutant_id for m in equivalence_candidates(mutants, decide, spec)}
    print("id,set,kind,equivalence_candidate,change")
    for mutant in mutants:
        group = "feedback" if mutant.mutant_id in feedback_ids else "evaluation"
        flag = "yes" if mutant.mutant_id in candidates else "no"
        print(f"{mutant.mutant_id},{group},{mutant.kind},{flag},{mutant.description}")


if __name__ == "__main__":
    main()

"""Structured specification: inputs, outputs, requirements and boundaries."""

from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
AEB_SPEC = ROOT / "requirements" / "aeb_requirements.yaml"

POSITIONS = ("below", "at", "above")


@dataclass(frozen=True)
class BoundaryPoint:
    boundary_id: str
    input: str
    value: float
    position: str
    strict_when: tuple

    @property
    def key(self):
        return (self.boundary_id, self.position)

    def describe(self):
        where = {"below": "just below", "at": "exactly at", "above": "just above"}[self.position]
        return f"{self.input} = {self.value:g} ({where} the {self.boundary_id} boundary)"


@dataclass(frozen=True)
class Spec:
    system: str
    description: str
    inputs: dict
    outputs: tuple
    requirements: tuple
    notes: tuple
    boundaries: tuple
    conditions: tuple = ()
    partitions: tuple = ()
    priority: tuple = ()
    fallback: str = ""

    def points(self):
        """Three points per boundary: value - resolution, value, value + resolution."""
        result = []
        for boundary in self.boundaries:
            step = self.inputs[boundary["input"]]["resolution"]
            conditions = tuple(sorted((boundary.get("strict_when") or {}).items()))
            for position, offset in zip(POSITIONS, (-step, 0, step)):
                result.append(
                    BoundaryPoint(
                        boundary_id=boundary["id"],
                        input=boundary["input"],
                        value=round(boundary["value"] + offset, 6),
                        position=position,
                        strict_when=conditions,
                    )
                )
        return result

    def holds(self, condition, test):
        """Decide one atomic condition for the inputs of a test."""
        value = test.value_of(condition["input"])
        if condition["op"] == "present":
            return value is not None
        if value is None:
            return False
        target = condition["value"]
        return {
            "<": value < target, "<=": value <= target, ">": value > target, ">=": value >= target,
        }[condition["op"]]

    def facts(self, test):
        """{condition id: True or False} for the inputs of a test."""
        return {c["id"]: self.holds(c, test) for c in self.conditions}

    def fact_text(self, test):
        """The conditions as sentences with yes or no, for a prompt."""
        facts = self.facts(test)
        return "; ".join(f"{c['text']}: {'yes' if facts[c['id']] else 'no'}" for c in self.conditions)

    def partition_of(self, test):
        """ID of the input class the inputs of a test belong to, or None."""
        facts = self.facts(test)
        for partition in self.partitions:
            if all(facts[cid] == wanted for cid, wanted in partition["when"].items()):
                return partition["id"]
        return None

    def order_text(self):
        """The order in which the requirements are applied, as an instruction. Names no output."""
        if not self.priority:
            return ""
        steps = ", then ".join(self.priority)
        text = ("Go through the requirements one at a time in this order and stop at the first one "
                f"whose condition holds: {steps}.")
        return text + (f" If none holds, {self.fallback} applies." if self.fallback else "")

    def condition_table_text(self):
        """The conditions with their IDs, for the prompt that asks for decision rules."""
        return "\n".join(f"- {c['id']}: {c['text']}" for c in self.conditions)

    def condition_text(self):
        return "\n".join(f"- {c['text']}" for c in self.conditions)

    def requirement_text(self):
        lines = [f"{r['id']}: {r['text']}" for r in self.requirements]
        lines += [f"Note: {note}" for note in self.notes]
        return "\n".join(lines)

    def input_text(self):
        lines = []
        for name, info in self.inputs.items():
            empty = ", may be empty" if info.get("nullable") else ""
            lines.append(f"{name}: {info['type']}, unit {info['unit']}, resolution {info['resolution']}{empty}")
        return "\n".join(lines)

    def boundary_text(self):
        return "\n".join(
            f"{b['id']}: {b['input']} = {b['value']:g}" for b in self.boundaries
        )


def load_spec(path=AEB_SPEC):
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Spec(
        system=raw["system"],
        description=" ".join(raw["description"].split()),
        inputs=raw["inputs"],
        outputs=tuple(raw["outputs"]),
        requirements=tuple(raw["requirements"]),
        notes=tuple(raw.get("notes") or ()),
        boundaries=tuple(raw["boundaries"]),
        conditions=tuple(raw.get("conditions") or ()),
        partitions=tuple(raw.get("partitions") or ()),
        priority=tuple((raw.get("priority") or {}).get("order") or ()),
        fallback=(raw.get("priority") or {}).get("otherwise") or "",
    )

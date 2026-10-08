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
    )

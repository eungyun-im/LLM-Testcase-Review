"""A stand-in for an LLM, used to exercise the pipeline without API calls.

It is NOT a model of any real LLM. It produces test sets with adjustable
flaws (missing boundary points, wrong expected results) and reacts to feedback
the way the pipeline expects, so that every code path runs in CI. Numbers
produced with it say nothing about real models and must never be reported as
results.
"""

import random

from tcgen.llm import LLMResponse
from tcgen.mutation import distinguishing_input, probe_inputs
from tcgen.schema import TestCase, to_csv

PROFILES = {
    # share of boundary points included, probability of a wrong expected result
    "b0": {"point_share": 0.35, "wrong": 0.15},
    "b1": {"point_share": 0.70, "wrong": 0.08},
}
NOMINAL = [
    ("REQ-01", 40.0, 10.0, 50),
    ("REQ-01", 80.0, 5.0, 20),
    ("REQ-02", 10.0, 10.0, 50),
    ("REQ-02", 20.0, None, 50),
    ("REQ-03", 40.0, 10.0, 300),
    ("REQ-05", 300.0, 10.0, 50),
    ("REQ-05", -5.0, None, 50),
]
CONTEXT = {"speed_kph": 40.0, "obstacle_m": 10.0, "sensor_age_ms": 50}


class SimulatedLLM:
    name = "simulated"
    model = "simulated"
    effort = "none"

    def __init__(self, spec, reference, seed=0):
        self.spec = spec
        self.reference = reference
        self.rng = random.Random(seed)
        self._probes = probe_inputs(spec)

    def complete(self, prompt, kind="generate", meta=None):
        meta = meta or {}
        handler = {
            "generate": self._generate,
            "feedback": self._feedback,
            "extend": self._extend,
            "cross_check": self._cross_check,
        }[kind]
        text = handler(meta)
        return LLMResponse(text=text, input_tokens=len(prompt) // 4, output_tokens=len(text) // 4)

    def _expected(self, inputs, wrong):
        correct = self.reference(*inputs).value
        if self.rng.random() < wrong:
            return self.rng.choice([o for o in self.spec.outputs if o != correct])
        return correct

    def _case(self, number, req_id, inputs, wrong):
        return TestCase(f"TC-{number:02d}", req_id, *inputs, self._expected(inputs, wrong))

    def _point_inputs(self, point):
        values = dict(CONTEXT, **{point.input: point.value})
        return (values["speed_kph"], values["obstacle_m"], int(values["sensor_age_ms"]))

    def _generate(self, meta):
        profile = PROFILES[meta.get("level", "b0")]
        tests = [
            self._case(i, req, (speed, obstacle, age), profile["wrong"])
            for i, (req, speed, obstacle, age) in enumerate(NOMINAL, start=1)
        ]
        for point in self.spec.points():
            if self.rng.random() < profile["point_share"]:
                tests.append(self._case(len(tests) + 1, "REQ-01", self._point_inputs(point), profile["wrong"]))
        return "Here are the test cases.\n\n```csv\n" + to_csv(tests) + "```\n"

    def _feedback(self, meta):
        tests = list(meta["tests"])
        flagged = meta.get("flagged", {})
        tests = [
            TestCase(t.tc_id, t.req_id, *t.inputs, flagged[t.tc_id])
            if t.tc_id in flagged and self.rng.random() < 0.8
            else t
            for t in tests
        ]
        tests += self._additions(meta, len(tests))
        return "```csv\n" + to_csv(tests) + "```\n"

    def _additions(self, meta, number):
        """Tests that answer the findings in meta, numbered after `number`."""
        added = []
        for point in meta.get("missing", []):
            added.append(self._case(number + len(added) + 1, "REQ-01", self._point_inputs(point), 0.05))
        for partition in meta.get("classes", []):
            probe = next(
                (p for p in self._probes
                 if self.spec.partition_of(TestCase("probe", "", *p, "")) == partition["id"]),
                None,
            )
            if probe is not None:
                added.append(self._case(number + len(added) + 1, "REQ-01", probe, 0.05))
        for mutant in meta.get("survivors", []):
            probe = distinguishing_input(mutant.load(), self.reference, self._probes)
            if probe is not None and self.rng.random() < 0.7:
                added.append(self._case(number + len(added) + 1, "REQ-01", probe, 0.05))
        return added

    def _extend(self, meta):
        return "```csv\n" + to_csv(self._additions(meta, len(meta["tests"]))) + "```\n"

    def _cross_check(self, meta):
        lines = ["tc_id,expected"]
        for test in meta["tests"]:
            lines.append(f"{test.tc_id},{self._expected(test.inputs, 0.05)}")
        return "\n".join(lines) + "\n"

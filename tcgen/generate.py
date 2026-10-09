"""Single-shot generation: B0 (requirements only) and B1 (enhanced prompt)."""

from tcgen.schema import parse_csv
from tcgen.spec import ROOT

PROMPTS = ROOT / "prompts"


def load_prompt(name):
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def build_prompt(level, spec):
    template = load_prompt(level)
    return template.format(
        system=spec.system,
        description=spec.description,
        requirements=spec.requirement_text(),
        inputs=spec.input_text(),
        outputs=", ".join(spec.outputs),
        boundaries=spec.boundary_text(),
        conditions=spec.condition_text(),
    )


def generate(llm, spec, level):
    """Return (tests, format_errors, calls). level is "b0" or "b1"."""
    prompt = build_prompt(level, spec)
    response = llm.complete(prompt, kind="generate", meta={"level": level})
    tests, format_errors = parse_csv(response.text, spec.outputs)
    call = {"round": 0, "kind": "generate", "prompt": prompt, "response": response}
    return tests, format_errors, [call]

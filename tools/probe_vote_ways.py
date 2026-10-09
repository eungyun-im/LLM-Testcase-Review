"""Which way of asking the grounded vote is most accurate? Five ways, the same 120 tests.

    python tools/probe_vote_ways.py qwen2.5:7b      (from the repository root, with Ollama running)

The tests are a random sample (seed 0) of the final FR test sets of results/confirm/qwen2.5-7b.db.
Results of 2026-10-09 are in results/extension/vote-probe.md. Exploratory.
"""
import random
import re
import sqlite3
import sys
import time

sys.path.insert(0, ".")
from sut.aeb import decide  # noqa: E402
from tcgen.checks import _parse_votes  # noqa: E402
from tcgen.generate import load_prompt  # noqa: E402
from tcgen.llm import OpenAICompatibleClient  # noqa: E402
from tcgen.metrics import output_of  # noqa: E402
from tcgen.schema import TestCase  # noqa: E402
from tcgen.spec import load_spec  # noqa: E402

model = sys.argv[1]
spec = load_spec()
conn = sqlite3.connect("results/confirm/qwen2.5-7b.db")
rows = conn.execute(
    "SELECT t.* FROM tests t JOIN runs r ON r.id = t.run_id WHERE r.condition = 'FR' AND r.failure IS NULL").fetchall()
rng = random.Random(0)
rows = rng.sample(rows, 120)
tests = [TestCase(f"T{i:03d}", "", r[3], r[4], r[5], "") for i, r in enumerate(rows)]
# columns of the tests table: run_id, tc_id, req_id, speed_kph, obstacle_m, sensor_age_ms, expected, valid
llm = OpenAICompatibleClient(model)
base = dict(requirements=spec.requirement_text(), outputs=", ".join(spec.outputs))


def batched(size):
    right = 0
    for start in range(0, len(tests), size):
        chunk = tests[start:start + size]
        prompt = load_prompt("cross_check_grounded").format(
            tests="\n".join(f"{t.tc_id}: {spec.fact_text(t)}" for t in chunk), **base)
        votes = _parse_votes(llm.complete(prompt, kind="cross_check").text)
        right += sum(votes.get(t.tc_id) == output_of(decide, t) for t in chunk)
    return right


def last_output(text):
    found = re.findall("|".join(spec.outputs), text.upper().replace(" ", "_"))
    return found[-1] if found else None


ORDER = ("Go through the requirements one at a time in this order and stop at the first one whose condition "
         "holds: REQ-05, then REQ-03, then REQ-01. If none holds, REQ-02 applies.")


def single(style):
    right = 0
    for t in tests:
        facts = spec.fact_text(t)
        if style == "plain":
            ask = "Reply with the output only."
        elif style == "reason":
            ask = "Think step by step in at most four short lines, then write a last line `answer: <output>`."
        else:
            ask = ORDER + " Think step by step in at most four short lines, then write a last line `answer: <output>`."
        prompt = (f"Requirements:\n{base['requirements']}\n\nPossible outputs: {base['outputs']}\n\n"
                  f"The conditions of the requirements have already been decided by a program for this case. "
                  f"Take each yes and no as given.\n\n{facts}\n\n{ask}")
        text = llm.complete(prompt, kind="cross_check").text
        right += last_output(text) == output_of(decide, t)
    return right


for name, run in (
    ("batch of 40 (current)", lambda: batched(40)),
    ("batch of 5", lambda: batched(5)),
    ("one test per call", lambda: single("plain")),
    ("one per call, step by step", lambda: single("reason")),
    ("one per call, step by step, order given", lambda: single("order")),
):
    started = time.time()
    right = run()
    print(f"{name:42} {right}/{len(tests)} = {right / len(tests):.0%}  ({time.time() - started:.0f} s)", flush=True)

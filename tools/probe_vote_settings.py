"""Accuracy of the ordered vote for a temperature and a number of votes.

    python tools/probe_vote_settings.py MODEL DB CONDITION TEMPERATURE VOTES [N]

Draws N tests (default 120, seed 0) from the final test sets of CONDITION in DB and
asks the ordered vote about each, VOTES times. Prints the accuracy of a single vote,
of the majority and of the unanimous results. Run from the repository root with
Ollama running. Only the test inputs are used; the stated results are ignored.
"""

import random
import sqlite3
import sys
import time
from collections import Counter

sys.path.insert(0, ".")
from sut.aeb import decide  # noqa: E402
from tcgen.checks import last_output, load_prompt  # noqa: E402
from tcgen.llm import OpenAICompatibleClient  # noqa: E402
from tcgen.metrics import output_of  # noqa: E402
from tcgen.schema import TestCase  # noqa: E402
from tcgen.spec import load_spec  # noqa: E402

model, db, condition, temperature, votes = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), int(sys.argv[5])
count = int(sys.argv[6]) if len(sys.argv) > 6 else 120
spec = load_spec()
rows = sqlite3.connect(db).execute(
    "SELECT t.* FROM tests t JOIN runs r ON r.id = t.run_id WHERE r.condition = ? AND r.failure IS NULL", (condition,)
).fetchall()
rows = random.Random(0).sample(rows, min(count, len(rows)))
tests = [TestCase(f"T{i:03d}", "", r[3], r[4], r[5], "") for i, r in enumerate(rows)]
truth = [output_of(decide, t) for t in tests]
llm = OpenAICompatibleClient(model, temperature=temperature if temperature >= 0 else None)
template = load_prompt("cross_check_ordered")
started = time.time()
ballots = []
for test in tests:
    prompt = template.format(
        requirements=spec.requirement_text(), outputs=", ".join(spec.outputs), tc_id=test.tc_id,
        facts=spec.fact_text(test), order=spec.order_text())
    ballots.append([last_output(llm.complete(prompt, kind="cross_check").text, spec.outputs) for _ in range(votes)])
single = sum(a == truth[i] for i, answers in enumerate(ballots) for a in answers) / (votes * len(tests))
majority = unanimous = unanimous_right = 0
for i, answers in enumerate(ballots):
    found = [a for a in answers if a]
    if not found:
        continue
    winner, top = Counter(found).most_common(1)[0]
    if top > votes / 2:
        majority += winner == truth[i]
    if top == votes and len(found) == votes:
        unanimous += 1
        unanimous_right += winner == truth[i]
print(f"temperature {temperature:g}, {votes} votes, {len(tests)} tests: single {single:.1%}, "
      f"majority right {majority / len(tests):.1%}, unanimous {unanimous / len(tests):.0%} "
      f"and right {unanimous_right / max(unanimous, 1):.1%} ({time.time() - started:.0f} s)")

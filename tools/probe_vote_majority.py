"""The two best ways of asking the vote, with majorities of three. The same 120 tests.

    python tools/probe_vote_majority.py qwen2.5:7b  (from the repository root, with Ollama running)

Results of 2026-10-09 are in results/extension/vote-probe.md. Exploratory.
"""
import random
import re
import sqlite3
import sys
import time
from collections import Counter

sys.path.insert(0, ".")
from sut.aeb import decide  # noqa: E402
from tcgen.llm import OpenAICompatibleClient  # noqa: E402
from tcgen.metrics import output_of  # noqa: E402
from tcgen.schema import TestCase  # noqa: E402
from tcgen.spec import load_spec  # noqa: E402

spec = load_spec()
rows = sqlite3.connect("results/confirm/qwen2.5-7b.db").execute(
    "SELECT t.* FROM tests t JOIN runs r ON r.id = t.run_id WHERE r.condition = 'FR' AND r.failure IS NULL").fetchall()
rows = random.Random(0).sample(rows, 120)
tests = [TestCase(f"T{i:03d}", "", r[3], r[4], r[5], "") for i, r in enumerate(rows)]
truth = [output_of(decide, t) for t in tests]
llm = OpenAICompatibleClient(sys.argv[1])
REQ = spec.requirement_text()
OUT = ", ".join(spec.outputs)
ORDER = ("Go through the requirements one at a time in this order and stop at the first one whose condition "
         "holds: REQ-05, then REQ-03, then REQ-01. If none holds, REQ-02 applies.")
INTRO = ("The conditions of the requirements have already been decided by a program for this case. "
         "Take each yes and no as given.")


def last_output(text):
    found = re.findall("|".join(spec.outputs), text.upper().replace(" ", "_"))
    return found[-1] if found else None


def ask(test, reason):
    tail = ("Think step by step in at most four short lines, then write a last line `answer: <output>`."
            if reason else "Reply with the output only.")
    prompt = (f"Requirements:\n{REQ}\n\nPossible outputs: {OUT}\n\n{INTRO}\n\n{spec.fact_text(test)}\n\n{ORDER} {tail}")
    return last_output(llm.complete(prompt, kind="cross_check").text)


for name, reason in (("order given, answer only", False), ("order given, step by step", True)):
    started = time.time()
    ballots = [[ask(t, reason) for t in tests] for _ in range(3)]
    single = sum(b[i] == truth[i] for b in ballots for i in range(len(tests))) / (3 * len(tests))
    majority, unanimous, unanimous_right = 0, 0, 0
    for i in range(len(tests)):
        answers = [b[i] for b in ballots if b[i]]
        if not answers:
            continue
        winner, count = Counter(answers).most_common(1)[0]
        majority += winner == truth[i] if count >= 2 else 0
        if len(answers) == 3 and count == 3:
            unanimous += 1
            unanimous_right += winner == truth[i]
    print(f"{name:28} single {single:.0%}, majority of three right {majority / len(tests):.0%}, "
          f"unanimous {unanimous / len(tests):.0%} and right {unanimous_right / max(unanimous, 1):.0%} "
          f"({time.time() - started:.0f} s)", flush=True)

"""The decision table: the requirements translated once, then applied by the program."""

import pytest

from sut.aeb import decide
from tcgen import mutation
from tcgen.analysis import rule_tables
from tcgen.checks import RuleTable, formalize, parse_rule_table
from tcgen.experiment import FR_VARIANTS
from tcgen.llm import ScriptedClient
from tcgen.metrics import output_of
from tcgen.refine import ALL_CHECKS, extend
from tcgen.schema import TestCase
from tcgen.spec import load_spec
from tcgen import store

SPEC = load_spec()
PROBES = [TestCase(f"P{i}", "", *inputs, "") for i, inputs in enumerate(mutation.probe_inputs(SPEC))]

RIGHT = """```csv
rule,when,then
1,C-SPEED-LOW=yes,FAULT
2,C-SPEED-HIGH=yes,FAULT
3,C-SENSOR-OLD=yes,FAULT
4,C-SPEED-BRAKE=yes; C-OBSTACLE=yes; C-IN-RANGE=yes,BRAKE
5,otherwise,NO_ACTION
```"""
# The two most natural mistakes: the order of the first rules, and a missing condition
SENSOR_FIRST = RIGHT.replace("1,C-SPEED-LOW=yes,FAULT\n2,C-SPEED-HIGH=yes,FAULT\n3,C-SENSOR-OLD=yes,FAULT",
                             "1,C-SENSOR-OLD=yes,FAULT\n2,C-SPEED-LOW=yes,FAULT\n3,C-SPEED-HIGH=yes,FAULT")
BRAKE_WITHOUT_RANGE = RIGHT.replace("C-SPEED-BRAKE=yes; C-OBSTACLE=yes; C-IN-RANGE=yes", "C-SPEED-BRAKE=yes; C-OBSTACLE=yes")


def case(tc_id, speed, obstacle, age, expected="NO_ACTION"):
    return TestCase(tc_id, "REQ-01", speed, obstacle, age, expected)


def disagreements(table):
    return sum((table.apply(SPEC, p) or "NONE") != output_of(decide, p) for p in PROBES)


def test_the_right_table_decides_every_probe_like_the_reference():
    assert disagreements(parse_rule_table(RIGHT, SPEC)) == 0


def test_a_swapped_order_is_a_systematic_error_not_a_random_one():
    # Equal outputs here, so it is invisible: a reminder that the order only matters where rules overlap
    table = parse_rule_table(SENSOR_FIRST, SPEC)
    assert disagreements(table) == 0
    # A rule that really changes the answer
    wrong = parse_rule_table(BRAKE_WITHOUT_RANGE, SPEC)
    far = case("T", 50.0, 100.0, 50)
    assert wrong.apply(SPEC, far) == "BRAKE" and decide(*far.inputs).value == "NO_ACTION"
    assert disagreements(wrong) > 0


def test_first_matching_rule_wins():
    table = RuleTable(((((("C-SENSOR-OLD", True),), "FAULT")), (((), "NO_ACTION"))))
    assert table.apply(SPEC, case("T", 40.0, 10.0, 300)) == "FAULT"
    assert table.apply(SPEC, case("T", 40.0, 10.0, 50)) == "NO_ACTION"


@pytest.mark.parametrize(
    "text",
    [
        "no table here",
        "rule,when,then\n1,C-SPEED-LOW=yes,EXPLODE\n",             # not an output
        "rule,when,then\n1,C-MADE-UP=yes,FAULT\n",                 # not a condition
        "rule,when,then\n1,C-SPEED-LOW=maybe,FAULT\n",             # not yes or no
        "rule,when,then\n",                                          # no rules
    ],
)
def test_a_table_that_would_need_guessing_is_unusable(text):
    assert parse_rule_table(text, SPEC) is None


def test_a_remark_and_case_are_forgiven():
    table = parse_rule_table("rule,when,then\n1,c-speed-low=YES,fault  # invalid speed\n2,else,no_action\n", SPEC)
    assert table.rules == (((("C-SPEED-LOW", True),), "FAULT"), ((), "NO_ACTION"))


def test_formalize_asks_for_the_table_once_per_vote_and_takes_the_most_common():
    llm = ScriptedClient([RIGHT, BRAKE_WITHOUT_RANGE, RIGHT])
    table, calls = formalize(llm, SPEC)
    assert len(calls) == 3 and {c["kind"] for c in calls} == {"formalize"}
    assert disagreements(table) == 0
    prompt = llm.calls[0][1]
    assert "C-SENSOR-OLD" in prompt and "first rule whose conditions are all met" in prompt


def test_unusable_answers_are_skipped_and_all_unusable_gives_no_table():
    assert formalize(ScriptedClient(["nope", RIGHT, "nope"]), SPEC)[0] is not None
    assert formalize(ScriptedClient(["nope"] * 3), SPEC)[0] is None


def test_the_table_decides_the_expected_results_in_extend():
    # Stated results are wrong on purpose. The table, not the model's statement, ends up in the test set.
    start = [case("T1", 40.0, 10.0, 50, "NO_ACTION"), case("T2", 40.0, 10.0, 300, "BRAKE"), case("T3", 10.0, None, 50, "FAULT")]
    llm = ScriptedClient([RIGHT] * 3)
    result, _, calls, rounds = extend(llm, SPEC, start, [], decide, enabled={"rules"})
    assert [t.expected for t in result] == ["BRAKE", "FAULT", "NO_ACTION"]
    assert rounds == 0 and [c["kind"] for c in calls] == ["formalize"] * 3


def test_without_a_usable_table_the_stated_results_stay():
    start = [case("T1", 40.0, 10.0, 50, "NO_ACTION")]
    result, _, _, _ = extend(ScriptedClient(["nope"] * 3), SPEC, start, [], decide, enabled={"rules"})
    assert result == start


def test_the_prompt_for_rules_contains_no_test_values():
    llm = ScriptedClient([RIGHT] * 3)
    extend(llm, SPEC, [case("T1", 47.3, 13.7, 123)], [], decide, enabled={"rules"})
    assert not any(value in llm.calls[0][1] for value in ("47.3", "13.7", "123"))


def test_variant_replaces_exactly_the_vote_by_the_table():
    procedure, enabled = FR_VARIANTS["FR-rules"]
    assert procedure is extend and enabled == (ALL_CHECKS - {"cross"}) | {"rules"}


def test_the_analysis_grades_the_stored_tables():
    conn = store.connect()
    run = conn.execute(
        "INSERT INTO runs (system, condition, repetition, client, model, effort, started_at, rounds, format_errors)"
        " VALUES ('AEB-lite', 'FR-rules', 1, 'scripted', 'scripted', 'none', '2026-10-09', 0, 0)"
    ).lastrowid
    for text in (RIGHT, BRAKE_WITHOUT_RANGE, "unusable"):
        conn.execute(
            "INSERT INTO llm_calls (run_id, round, kind, prompt, response, input_tokens, output_tokens, duration_ms)"
            " VALUES (?, 1, 'formalize', 'p', ?, 0, 0, 0)", (run, text))
    result = rule_tables(conn, SPEC)
    assert result["unusable"] == 1 and len(result["votes"]) == 2
    assert result["votes"][0] == 0 and result["votes"][1] > 0
    assert result["chosen"][0] in result["votes"]

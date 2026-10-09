"""The vote asked one test at a time, with the order of the requirements given."""

from sut.aeb import decide
from tcgen import store
from tcgen.analysis import final_votes
from tcgen.checks import last_output, ordered_vote, votes_in
from tcgen.experiment import FR_VARIANTS
from tcgen.llm import ScriptedClient
from tcgen.refine import ALL_CHECKS, extend
from tcgen.schema import TestCase
from tcgen.spec import load_spec

SPEC = load_spec()


def case(tc_id, speed, obstacle, age, expected="NO_ACTION"):
    return TestCase(tc_id, "REQ-01", speed, obstacle, age, expected)


def test_the_order_is_printed_as_a_procedure_and_names_no_output():
    text = SPEC.order_text()
    assert "REQ-05, then REQ-03, then REQ-01" in text and "If none holds, REQ-02 applies" in text
    assert not any(output in text for output in SPEC.outputs)


def test_an_answer_is_read_from_a_short_reply():
    assert last_output("no action", SPEC.outputs) == "NO_ACTION"
    assert last_output("Step 1: FAULT?\nanswer: BRAKE", SPEC.outputs) == "BRAKE"
    assert last_output("I cannot tell.", SPEC.outputs) is None


def test_one_question_per_test_and_vote_with_facts_only():
    tests = [case("T1", 47.3, 13.7, 123, "BRAKE"), case("T2", 10.0, None, 50, "FAULT")]
    llm = ScriptedClient(["BRAKE", "BRAKE", "BRAKE", "NO_ACTION", "NO_ACTION", "NO_ACTION"])
    flagged, calls, unanimous = ordered_vote(tests, llm, SPEC)
    assert len(calls) == 6
    prompt = llm.calls[0][1]
    assert "Case T1:" in prompt and "REQ-05, then REQ-03, then REQ-01" in prompt
    assert not any(value in prompt for value in ("47.3", "13.7", "123"))
    assert flagged == {"T2": "NO_ACTION"}          # the stated FAULT loses to the majority
    assert unanimous == {"T1": "BRAKE", "T2": "NO_ACTION"}


def test_a_split_vote_is_decided_by_the_majority_and_is_not_unanimous():
    tests = [case("T1", 40.0, 10.0, 50, "NO_ACTION")]
    flagged, _, unanimous = ordered_vote(tests, ScriptedClient(["BRAKE", "BRAKE", "FAULT"]), SPEC)
    assert flagged == {"T1": "BRAKE"} and unanimous == {}


def test_without_a_majority_the_stated_result_stays():
    tests = [case("T1", 40.0, 10.0, 50, "NO_ACTION")]
    flagged, _, unanimous = ordered_vote(tests, ScriptedClient(["BRAKE", "FAULT", "NO_ACTION"]), SPEC)
    assert flagged == {} and unanimous == {}


def test_extend_applies_the_ordered_majority():
    start = [case("T1", 40.0, 10.0, 50, "NO_ACTION")]
    result, _, calls, _ = extend(ScriptedClient(["BRAKE"] * 3), SPEC, start, [], decide, enabled={"cross-ordered"})
    assert [t.expected for t in result] == ["BRAKE"]
    assert len(calls) == 3 and {c["kind"] for c in calls} == {"cross_check"}


def test_variant_replaces_exactly_the_vote_form():
    procedure, enabled = FR_VARIANTS["FR-ordered"]
    assert procedure is extend and enabled == (ALL_CHECKS - {"cross"}) | {"cross-ordered"}


def test_votes_are_read_back_from_either_stored_form():
    assert votes_in("Case T9: x", "FAULT", SPEC.outputs) == {"T9": "FAULT"}
    assert votes_in("anything", "tc_id,expected\nT1,BRAKE", SPEC.outputs) == {"T1": "BRAKE"}


def test_the_analysis_grades_votes_asked_one_at_a_time():
    conn = store.connect()
    run = conn.execute(
        "INSERT INTO runs (system, condition, repetition, client, model, effort, started_at, rounds, format_errors)"
        " VALUES ('AEB-lite', 'FR-ordered', 1, 'scripted', 'scripted', 'none', '2026-10-09', 0, 0)"
    ).lastrowid
    conn.execute(
        "INSERT INTO tests (run_id, tc_id, req_id, speed_kph, obstacle_m, sensor_age_ms, expected, valid)"
        " VALUES (?, 'T1', 'REQ-01', 40.0, 10.0, 300, 'FAULT', 1)", (run,))
    for answer in ("FAULT", "FAULT", "BRAKE"):
        conn.execute(
            "INSERT INTO llm_calls (run_id, round, kind, prompt, response, input_tokens, output_tokens, duration_ms)"
            " VALUES (?, 1, 'cross_check', 'Case T1: facts', ?, 0, 0, 0)", (run, answer))
    tally = final_votes(conn, SPEC.outputs)["FR-ordered"]
    assert (tally["votes"], tally["votes right"], tally["majority right"], tally["unanimous"]) == (3, 2, 1, 0)

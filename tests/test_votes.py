"""Grading of the final vote of the additive procedure."""

from tcgen import store
from tcgen.analysis import final_votes
from tcgen.spec import load_spec

SPEC = load_spec()


def test_the_final_vote_is_graded_against_the_reference():
    conn = store.connect()
    run = conn.execute(
        "INSERT INTO runs (system, condition, repetition, client, model, effort, started_at, rounds, format_errors)"
        " VALUES ('AEB-lite', 'FR', 1, 'scripted', 'scripted', 'none', '2026-10-09', 0, 0)"
    ).lastrowid
    # T1 is a brake case, T2 a case with sensor data too old: the right answers are BRAKE and FAULT
    for tc_id, age in (("T1", 50), ("T2", 300)):
        conn.execute(
            "INSERT INTO tests (run_id, tc_id, req_id, speed_kph, obstacle_m, sensor_age_ms, expected, valid)"
            " VALUES (?, ?, 'REQ-01', 40.0, 10.0, ?, 'BRAKE', 1)",
            (run, tc_id, age),
        )
    for second in ("BRAKE", "FAULT", "BRAKE"):
        conn.execute(
            "INSERT INTO llm_calls (run_id, round, kind, prompt, response, input_tokens, output_tokens, duration_ms)"
            " VALUES (?, 1, 'cross_check', 'p', ?, 0, 0, 0)",
            (run, f"tc_id,expected\nT1,BRAKE\nT2,{second}"),
        )
    tally = final_votes(conn, SPEC.outputs)["FR"]
    assert (tally["tests"], tally["votes"], tally["votes right"]) == (2, 6, 4)
    assert (tally["majority"], tally["majority right"]) == (2, 1)    # T2: the majority says BRAKE, which is wrong
    assert (tally["unanimous"], tally["unanimous right"]) == (1, 1)  # only T1 is unanimous


def test_the_rewrite_loop_is_not_part_of_this_grading():
    conn = store.connect()
    run = conn.execute(
        "INSERT INTO runs (system, condition, repetition, client, model, effort, started_at, rounds, format_errors)"
        " VALUES ('AEB-lite', 'FR-rewrite', 1, 'scripted', 'scripted', 'none', '2026-10-09', 1, 0)"
    ).lastrowid
    conn.execute(
        "INSERT INTO llm_calls (run_id, round, kind, prompt, response, input_tokens, output_tokens, duration_ms)"
        " VALUES (?, 1, 'cross_check', 'p', 'tc_id,expected\nT1,BRAKE', 0, 0, 0)",
        (run,),
    )
    assert final_votes(conn, SPEC.outputs) == {}

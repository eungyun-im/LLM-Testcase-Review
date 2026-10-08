"""End-to-end run of the pipeline on the simulator, plus statistics helpers."""

import pytest

from tcgen import report, stats, store
from tcgen.experiment import CONDITIONS, evaluate, make_context, run_human_baseline, run_repetition
from tcgen.llm import LLMError, ScriptedClient
from tcgen.schema import TestCase, to_csv
from tcgen.simulator import SimulatedLLM

CONTEXT = make_context()
REPS = 3


@pytest.fixture(scope="module")
def conn():
    connection = store.connect()
    llm = SimulatedLLM(CONTEXT.spec, CONTEXT.reference, seed=1)
    for repetition in range(1, REPS + 1):
        run_repetition(connection, llm, CONTEXT, repetition)
    yield connection
    connection.close()


def test_every_condition_is_stored_for_every_repetition(conn):
    rows = conn.execute("SELECT condition, COUNT(*) AS n FROM runs GROUP BY condition").fetchall()
    assert {row["condition"]: row["n"] for row in rows} == {name: REPS for name in CONDITIONS}


def test_prompts_and_raw_outputs_are_kept(conn):
    row = conn.execute("SELECT prompt, response FROM llm_calls WHERE kind = 'generate' LIMIT 1").fetchone()
    assert "REQ-01" in row["prompt"] and "tc_id" in row["response"]


def test_fr_starts_from_b1_and_costs_more(conn):
    b1 = store.metric_values(conn, "AEB-lite", "B1", "llm_calls")
    fr = store.metric_values(conn, "AEB-lite", "FR", "llm_calls")
    assert all(fr[rep] >= b1[rep] for rep in b1)
    no_cross = store.metric_values(conn, "AEB-lite", "FR-cross", "llm_calls")
    assert all(no_cross[rep] <= fr[rep] for rep in fr)


def test_metrics_are_recomputable_from_stored_tests(conn):
    run = conn.execute("SELECT id FROM runs WHERE condition = 'B1' ORDER BY id LIMIT 1").fetchone()["id"]
    rows = conn.execute("SELECT * FROM tests WHERE run_id = ?", (run,)).fetchall()
    tests = [
        TestCase(r["tc_id"], r["req_id"], r["speed_kph"], r["obstacle_m"], r["sensor_age_ms"], r["expected"])
        for r in rows
    ]
    stored = dict(conn.execute("SELECT name, value FROM metrics WHERE run_id = ?", (run,)).fetchall())
    again = evaluate(CONTEXT, tests)["metrics"]
    for name in ("error_rate", "boundary_recall_simple", "boundary_recall_strict", "detection_seeded", "detection_mutants"):
        assert again[name] == pytest.approx(stored[name])


def test_report_renders_and_flags_simulated_data(conn):
    text = report.render(conn)
    assert "Simulated data" in text
    assert "Table 1" in text and "Table 2" in text
    assert "F1" in text


def test_human_baseline_is_skipped_while_empty(tmp_path):
    connection = store.connect()
    empty = tmp_path / "baseline.csv"
    empty.write_text("tc_id,req_id,speed_kph,obstacle_m,sensor_age_ms,expected\n", encoding="utf-8")
    assert run_human_baseline(connection, CONTEXT, empty) is False
    filled = tmp_path / "filled.csv"
    filled.write_text(to_csv([TestCase("H-01", "REQ-01", 30.0, 10.0, 50, "BRAKE")]), encoding="utf-8")
    assert run_human_baseline(connection, CONTEXT, filled) is True
    row = connection.execute("SELECT client FROM runs WHERE condition = 'H'").fetchone()
    assert row["client"] == "human"


def test_a_failed_generation_is_recorded_not_raised():
    class Refusing(ScriptedClient):
        def complete(self, prompt, kind="generate", meta=None):
            raise LLMError("refused")

    connection = store.connect()
    run_repetition(connection, Refusing([]), CONTEXT, 1)
    rows = connection.execute("SELECT condition, failure FROM runs").fetchall()
    assert len(rows) == len(CONDITIONS)
    assert all(row["failure"] for row in rows)


def test_a12():
    assert stats.a12([1, 2, 3], [1, 2, 3]) == 0.5
    assert stats.a12([4, 5, 6], [1, 2, 3]) == 1.0
    assert stats.a12([1, 2], [3, 4]) == 0.0


def test_holm_adjustment():
    adjusted = stats.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adjusted["a"] == pytest.approx(0.03)
    assert adjusted["c"] == pytest.approx(0.06)
    assert adjusted["b"] == pytest.approx(0.06)


def test_paired_test_handles_identical_samples():
    assert stats.wilcoxon_p([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]) == 1.0

"""SQLite store for experiment runs."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def connect(path=":memory:"):
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'runs'"
    ).fetchone()
    if not exists:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.commit()
    return conn


def save_run(conn, *, system, condition, repetition, llm, result):
    """Store one evaluated run. result is the dict built by experiment.evaluate()."""
    run_id = conn.execute(
        "INSERT INTO runs (system, condition, repetition, client, model, effort, started_at,"
        " rounds, format_errors, failure) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            system,
            condition,
            repetition,
            llm.name,
            llm.model,
            llm.effort,
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            result.get("rounds", 0),
            result.get("format_errors", 0),
            result.get("failure"),
        ),
    ).lastrowid
    conn.executemany(
        "INSERT INTO llm_calls (run_id, round, kind, prompt, response, input_tokens,"
        " output_tokens, duration_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                run_id,
                call["round"],
                call["kind"],
                call["prompt"],
                call["response"].text,
                call["response"].input_tokens,
                call["response"].output_tokens,
                call["response"].duration_ms,
            )
            for call in result.get("calls", [])
        ],
    )
    valid_ids = {t.tc_id for t in result.get("valid", [])}
    conn.executemany(
        "INSERT INTO tests (run_id, tc_id, req_id, speed_kph, obstacle_m, sensor_age_ms,"
        " expected, valid) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (run_id, t.tc_id, t.req_id, t.speed_kph, t.obstacle_m, t.sensor_age_ms, t.expected,
             int(t.tc_id in valid_ids))
            for t in result.get("tests", [])
        ],
    )
    conn.executemany(
        "INSERT INTO detections (run_id, defect_set, defect_id, detected) VALUES (?, ?, ?, ?)",
        [
            (run_id, defect_set, defect_id, int(found))
            for defect_set, table in result.get("detections", {}).items()
            for defect_id, found in table.items()
        ],
    )
    conn.executemany(
        "INSERT INTO metrics (run_id, name, value) VALUES (?, ?, ?)",
        [(run_id, name, float(value)) for name, value in result.get("metrics", {}).items()],
    )
    conn.commit()
    return run_id


def metric_values(conn, system, condition, name):
    """Values of one metric for a condition, ordered by repetition."""
    rows = conn.execute(
        "SELECT r.repetition, m.value FROM metrics AS m JOIN runs AS r ON r.id = m.run_id"
        " WHERE r.system = ? AND r.condition = ? AND m.name = ? AND r.failure IS NULL"
        " ORDER BY r.repetition",
        (system, condition, name),
    ).fetchall()
    return {row["repetition"]: row["value"] for row in rows}

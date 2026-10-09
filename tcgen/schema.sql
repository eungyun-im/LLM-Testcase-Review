-- Everything needed to recompute the metrics: prompts, raw model output,
-- the parsed tests, and which defect versions each run detected.

CREATE TABLE runs (
    id             INTEGER PRIMARY KEY,
    system         TEXT NOT NULL,
    condition      TEXT NOT NULL,              -- B0, B1, FR, FR-boundary, FR-cross, FR-mutation, H
    repetition     INTEGER NOT NULL,
    client         TEXT NOT NULL,              -- anthropic, simulated, human
    model          TEXT NOT NULL,
    effort         TEXT NOT NULL,
    started_at     TEXT NOT NULL,
    rounds         INTEGER NOT NULL DEFAULT 0, -- feedback rounds used
    format_errors  INTEGER NOT NULL DEFAULT 0,
    failure        TEXT                        -- set when the run produced no test set
);

CREATE TABLE llm_calls (
    id             INTEGER PRIMARY KEY,
    run_id         INTEGER NOT NULL REFERENCES runs(id),
    round          INTEGER NOT NULL,
    kind           TEXT NOT NULL CHECK (kind IN ('generate', 'feedback', 'extend', 'cross_check')),
    prompt         TEXT NOT NULL,
    response       TEXT NOT NULL,
    input_tokens   INTEGER NOT NULL,
    output_tokens  INTEGER NOT NULL,
    duration_ms    INTEGER NOT NULL
);

CREATE TABLE tests (
    run_id         INTEGER NOT NULL REFERENCES runs(id),
    tc_id          TEXT NOT NULL,
    req_id         TEXT NOT NULL,
    speed_kph      REAL NOT NULL,
    obstacle_m     REAL,
    sensor_age_ms  INTEGER NOT NULL,
    expected       TEXT NOT NULL,
    valid          INTEGER NOT NULL,           -- 1 when the reference implementation agrees
    PRIMARY KEY (run_id, tc_id)
);

CREATE TABLE detections (
    run_id      INTEGER NOT NULL REFERENCES runs(id),
    defect_set  TEXT NOT NULL CHECK (defect_set IN ('seeded', 'mutant')),
    defect_id   TEXT NOT NULL,
    detected    INTEGER NOT NULL,
    PRIMARY KEY (run_id, defect_set, defect_id)
);

CREATE TABLE metrics (
    run_id  INTEGER NOT NULL REFERENCES runs(id),
    name    TEXT NOT NULL,
    value   REAL NOT NULL,
    PRIMARY KEY (run_id, name)
);

CREATE INDEX idx_runs_condition ON runs(system, condition, repetition);

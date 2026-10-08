from dataclasses import dataclass
from typing import Optional

COLUMNS = [
    "tc_id",
    "req_id",
    "speed_kph",
    "obstacle_m",
    "sensor_age_ms",
    "expected",
    "technique",
    "rationale",
]

EXPECTED_VALUES = {"BRAKE", "NO_ACTION", "FAULT"}
DECISIONS = {"accept", "fix", "reject"}
REASON_CODES = {
    "wrong_expected",
    "missed_boundary",
    "duplicate",
    "not_in_requirement",
    "untestable",
}


@dataclass
class Candidate:
    tc_id: str
    req_id: str
    speed_kph: float
    obstacle_m: Optional[float]
    sensor_age_ms: int
    expected: str
    technique: str = ""
    rationale: str = ""

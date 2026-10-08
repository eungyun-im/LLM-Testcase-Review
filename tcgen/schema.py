"""Test case record and the CSV format every condition uses."""

import csv
import io
from dataclasses import dataclass
from typing import Optional

COLUMNS = ["tc_id", "req_id", "speed_kph", "obstacle_m", "sensor_age_ms", "expected"]
EMPTY_MARKERS = {"", "none", "null", "n/a", "-"}


@dataclass(frozen=True)
class TestCase:
    __test__ = False  # not a pytest test class

    tc_id: str
    req_id: str
    speed_kph: float
    obstacle_m: Optional[float]
    sensor_age_ms: int
    expected: str

    @property
    def inputs(self):
        return (self.speed_kph, self.obstacle_m, self.sensor_age_ms)

    def value_of(self, name):
        return getattr(self, name)


def _parse_row(row, outputs):
    obstacle = row["obstacle_m"].strip()
    age = float(row["sensor_age_ms"])
    if age != int(age):
        raise ValueError("sensor_age_ms must be an integer")
    expected = row["expected"].strip().upper()
    if expected not in outputs:
        raise ValueError(f"unknown expected result {expected!r}")
    return TestCase(
        tc_id=row["tc_id"].strip(),
        req_id=row["req_id"].strip(),
        speed_kph=float(row["speed_kph"]),
        obstacle_m=None if obstacle.lower() in EMPTY_MARKERS else float(obstacle),
        sensor_age_ms=int(age),
        expected=expected,
    )


def parse_csv(text, outputs):
    """Extract test cases from model output.

    Looks for the header line, then reads rows until the block ends. Returns
    (tests, format_errors): rows that cannot be parsed or that name an
    undefined output are counted, not repaired.
    """
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.replace(" ", "").lower().startswith("tc_id,")),
        None,
    )
    if start is None:
        return [], 0
    block = []
    for line in lines[start:]:
        if not line.strip() or line.strip().startswith("```"):
            break
        block.append(line)
    reader = csv.DictReader(io.StringIO("\n".join(block)), skipinitialspace=True)
    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
    tests, errors, seen = [], 0, set()
    for row in reader:
        try:
            test = _parse_row(row, outputs)
        except (KeyError, ValueError, AttributeError, TypeError):
            errors += 1
            continue
        if not test.tc_id or test.tc_id in seen:
            errors += 1
            continue
        seen.add(test.tc_id)
        tests.append(test)
    return tests, errors


def to_csv(tests, with_expected=True):
    columns = COLUMNS if with_expected else COLUMNS[:-1]
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(columns)
    for test in tests:
        row = [
            test.tc_id,
            test.req_id,
            f"{test.speed_kph:g}",
            "" if test.obstacle_m is None else f"{test.obstacle_m:g}",
            test.sensor_age_ms,
        ]
        writer.writerow(row + [test.expected] if with_expected else row)
    return out.getvalue()


def load_csv_file(path, outputs):
    with open(path, encoding="utf-8") as f:
        return parse_csv(f.read(), outputs)

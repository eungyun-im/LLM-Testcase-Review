import pytest

from sut.aeb import decide
from sut.defects import SEEDED
from tcgen import metrics
from tcgen.mutation import distinguishing_input, probe_inputs
from tcgen.schema import TestCase, parse_csv, to_csv
from tcgen.spec import load_spec

SPEC = load_spec()


def case(tc_id, speed, obstacle, age, expected):
    return TestCase(tc_id, "REQ-01", speed, obstacle, age, expected)


def test_spec_has_fifteen_boundary_points():
    points = SPEC.points()
    assert len(points) == 15
    speed_points = sorted(p.value for p in points if p.boundary_id == "B-BRAKE-SPEED")
    assert speed_points == [29.9, 30.0, 30.1]


def test_error_rate_counts_wrong_expected_results():
    tests = [
        case("T1", 40.0, 10.0, 50, "BRAKE"),
        case("T2", 30.0, 10.0, 50, "NO_ACTION"),  # wrong: 30.0 brakes
        case("T3", 40.0, None, 50, "NO_ACTION"),
        case("T4", 40.0, 10.0, 200, "BRAKE"),  # wrong: stale sensor
    ]
    assert metrics.error_rate(tests, decide) == 0.5
    valid, wrong = metrics.split_valid(tests, decide)
    assert [t.tc_id for t in valid] == ["T1", "T3"]
    assert [t.tc_id for t in wrong] == ["T2", "T4"]


def test_boundary_recall_two_of_three_points():
    tests = [case("T1", 29.9, 10.0, 50, "NO_ACTION"), case("T2", 30.0, 10.0, 50, "BRAKE")]
    simple, strict = metrics.boundary_recall(tests, SPEC)
    assert simple == pytest.approx(2 / 15)
    assert strict == pytest.approx(2 / 15)


def test_strict_recall_needs_a_revealing_context():
    # 30.0 km/h with the obstacle out of range: the speed boundary cannot show.
    tests = [case("T1", 30.0, 50.0, 50, "NO_ACTION")]
    simple, strict = metrics.boundary_recall(tests, SPEC)
    assert simple == pytest.approx(1 / 15)
    assert strict == 0.0


def test_no_obstacle_never_matches_a_distance_point():
    tests = [case("T1", 40.0, None, 50, "NO_ACTION")]
    covered, _, _ = metrics.boundary_coverage(tests, SPEC)
    assert all(p.input != "obstacle_m" for p in covered)


def test_detection_needs_a_test_that_fails_on_the_defect():
    versions = {defect_id: entry[2] for defect_id, entry in SEEDED.items()}
    nominal = [case("T1", 40.0, 10.0, 50, "BRAKE")]
    rate, table = metrics.detection(nominal, versions)
    assert rate == 0.0
    at_threshold = [case("T2", 30.0, 10.0, 50, "BRAKE")]
    _, table = metrics.detection(at_threshold, versions)
    assert table["F1"] is True
    assert table["F2"] is False


def test_excluded_versions_leave_the_denominator():
    versions = {defect_id: entry[2] for defect_id, entry in SEEDED.items()}
    tests = [case("T2", 30.0, 10.0, 50, "BRAKE")]
    rate, table = metrics.detection(tests, versions, excluded=set(versions) - {"F1"})
    assert rate == 1.0 and list(table) == ["F1"]


def test_every_seeded_defect_changes_behavior():
    probes = probe_inputs(SPEC)
    for defect_id, (_, _, defect) in SEEDED.items():
        assert distinguishing_input(defect, decide, probes) is not None, defect_id


def test_csv_round_trip():
    tests = [case("T1", 40.0, 10.0, 50, "BRAKE"), case("T2", 29.9, None, 199, "NO_ACTION")]
    parsed, errors = parse_csv(to_csv(tests), SPEC.outputs)
    assert parsed == tests and errors == 0


def test_parse_tolerates_surrounding_prose_and_counts_bad_rows():
    text = (
        "Here are the tests:\n\n```csv\n"
        "tc_id, req_id, speed_kph, obstacle_m, sensor_age_ms, expected\n"
        "TC-01, REQ-01, 40, 10, 50, brake\n"
        "TC-02, REQ-01, fast, 10, 50, BRAKE\n"
        "TC-03, REQ-01, 40, none, 50, NO_ACTION\n"
        "TC-04, REQ-01, 40, 10, 50, STOP\n"
        "TC-01, REQ-01, 41, 10, 50, BRAKE\n"
        "```\nLet me know if you need more."
    )
    parsed, errors = parse_csv(text, SPEC.outputs)
    assert [t.tc_id for t in parsed] == ["TC-01", "TC-03"]
    assert parsed[0].expected == "BRAKE" and parsed[1].obstacle_m is None
    assert errors == 3


def test_parse_without_a_table_returns_nothing():
    assert parse_csv("I cannot help with that.", SPEC.outputs) == ([], 0)


def test_blank_line_after_the_header_does_not_hide_the_table():
    # Seen in a pilot run: the model separated the header from the rows.
    text = (
        "tc_id,req_id,speed_kph,obstacle_m,sensor_age_ms,expected\n"
        "\n"
        "1,REQ-01,30.0,20.0,100,BRAKE\n"
        "2,REQ-02,29.9,20.0,100,NO_ACTION\n"
        "\n"
        "3,REQ-01,50.0,10.0,100,BRAKE\n"
    )
    parsed, errors = parse_csv(text, SPEC.outputs)
    assert [test.tc_id for test in parsed] == ["1", "2"]
    assert errors == 0


def test_remark_after_the_expected_result_is_ignored():
    text = (
        "tc_id,req_id,speed_kph,obstacle_m,sensor_age_ms,expected\n"
        "1,REQ-01,30.0,20.0,100,BRAKE  # added for the boundary\n"
        "2,REQ-02,29.9,20.0,100.0,no_action\n"
    )
    parsed, errors = parse_csv(text, SPEC.outputs)
    assert [(test.tc_id, test.expected, test.sensor_age_ms) for test in parsed] == [
        ("1", "BRAKE", 100), ("2", "NO_ACTION", 100),
    ]
    assert errors == 0


def test_rows_that_would_need_guessing_are_counted_not_repaired():
    text = (
        "tc_id,req_id,speed_kph,obstacle_m,sensor_age_ms,expected\n"
        "1,REQ-05,B-SPEED-MIN,speed_kph=0.9,20,200,FAULT\n"   # one column too many
        "2,REQ-02,29.9,20.0,100,No Action\n"                   # not a defined output
        "3,REQ-02,29.9,20.0,100,NO_ACTION\n"
    )
    parsed, errors = parse_csv(text, SPEC.outputs)
    assert [test.tc_id for test in parsed] == ["3"]
    assert errors == 2

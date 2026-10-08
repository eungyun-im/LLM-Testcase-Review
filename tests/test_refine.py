from sut.aeb import decide
from tcgen import mutation
from tcgen.checks import boundary_check, cross_check, mutation_check, render_feedback
from tcgen.llm import ScriptedClient
from tcgen.refine import refine
from tcgen.schema import TestCase, to_csv
from tcgen.spec import load_spec

SPEC = load_spec()
MUTANTS = mutation.generate()


def case(tc_id, speed, obstacle, age, expected):
    return TestCase(tc_id, "REQ-01", speed, obstacle, age, expected)


def complete_set():
    """One valid test per boundary point, each in a context that reveals the boundary."""
    context = {"speed_kph": 40.0, "obstacle_m": 10.0, "sensor_age_ms": 50}
    tests = []
    for number, point in enumerate(SPEC.points(), start=1):
        values = dict(context, **{point.input: point.value})
        inputs = (values["speed_kph"], values["obstacle_m"], int(values["sensor_age_ms"]))
        tests.append(TestCase(f"TC-{number:02d}", "REQ-01", *inputs, decide(*inputs).value))
    return tests


def votes(tests, overrides=None):
    overrides = overrides or {}
    rows = [f"{t.tc_id},{overrides.get(t.tc_id, t.expected)}" for t in tests]
    return "tc_id,expected\n" + "\n".join(rows)


def test_boundary_check_lists_missing_points():
    tests = [case("T1", 29.9, 10.0, 50, "NO_ACTION"), case("T2", 30.0, 10.0, 50, "BRAKE")]
    missing = boundary_check(tests, SPEC)
    assert len(missing) == 13
    assert ("B-BRAKE-SPEED", "above") in {p.key for p in missing}
    assert boundary_check(complete_set(), SPEC) == []


def test_cross_check_flags_only_majority_disagreement():
    tests = [case("T1", 30.0, 10.0, 50, "NO_ACTION"), case("T2", 40.0, 10.0, 50, "BRAKE")]
    llm = ScriptedClient(
        [
            votes(tests, {"T1": "BRAKE"}),
            votes(tests, {"T1": "BRAKE", "T2": "FAULT"}),
            votes(tests),
        ]
    )
    flagged, calls = cross_check(tests, llm, SPEC)
    assert flagged == {"T1": "BRAKE"}
    assert len(calls) == 3
    assert "NO_ACTION" not in llm.calls[0][1].split("Cases")[1]  # expected results are withheld


def test_mutation_check_ignores_expected_results():
    right = [case("T1", 30.0, 10.0, 50, "BRAKE")]
    wrong = [case("T1", 30.0, 10.0, 50, "FAULT")]
    assert mutation_check(right, MUTANTS, decide) == mutation_check(wrong, MUTANTS, decide)


def test_mutation_check_finds_survivors_of_a_weak_set():
    survivors = mutation_check([case("T1", 40.0, 10.0, 50, "BRAKE")], MUTANTS, decide)
    assert 0 < len(survivors) < len(MUTANTS)


def test_feedback_text_is_empty_without_findings():
    assert render_feedback([], {}, []) == ""


def test_refine_stops_when_checks_find_nothing():
    tests = complete_set()
    llm = ScriptedClient([])
    result, errors, calls, rounds = refine(llm, SPEC, tests, [], decide, enabled={"boundary", "mutation"})
    assert result == tests and rounds == 0 and calls == [] and errors == 0


def test_refine_applies_a_revision_then_stops():
    start = [case("T1", 40.0, 10.0, 50, "BRAKE")]
    llm = ScriptedClient(["```csv\n" + to_csv(complete_set()) + "```"])
    result, _, calls, rounds = refine(llm, SPEC, start, [], decide, enabled={"boundary"})
    assert rounds == 1
    assert [c["kind"] for c in calls] == ["feedback"]
    assert boundary_check(result, SPEC) == []
    assert "B-BRAKE-SPEED" in llm.calls[0][1]


def test_refine_gives_up_after_three_rounds():
    start = [case("T1", 40.0, 10.0, 50, "BRAKE")]
    unchanged = "```csv\n" + to_csv(start) + "```"
    llm = ScriptedClient([unchanged] * 5)
    _, _, calls, rounds = refine(llm, SPEC, start, [], decide, enabled={"boundary"})
    assert rounds == 3 and len(calls) == 3


def test_refine_keeps_the_previous_set_on_an_unusable_answer():
    start = [case("T1", 40.0, 10.0, 50, "BRAKE")]
    llm = ScriptedClient(["Sorry, I cannot produce that."])
    result, _, _, rounds = refine(llm, SPEC, start, [], decide, enabled={"boundary"})
    assert result == start and rounds == 1


def test_feedback_never_contains_reference_results():
    # T1 is wrong against the reference, but only the three checks may speak.
    start = [case("T1", 30.0, 10.0, 50, "NO_ACTION")]
    llm = ScriptedClient(["```csv\n" + to_csv(start) + "```"] * 3)
    refine(llm, SPEC, start, [], decide, enabled={"boundary"})
    prompt = llm.calls[0][1]
    assert "independent recomputation" not in prompt
    assert "fails" not in prompt.lower()

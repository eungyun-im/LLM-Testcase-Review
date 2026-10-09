"""Conditions, input classes and the grounded cross-check."""

from sut.aeb import decide
from tcgen import mutation
from tcgen.checks import cross_check, partition_check, render_feedback
from tcgen.experiment import FR_VARIANTS
from tcgen.llm import ScriptedClient
from tcgen.metrics import partition_coverage
from tcgen.refine import extend, refine
from tcgen.schema import TestCase, to_csv
from tcgen.spec import load_spec

SPEC = load_spec()
PROBES = [TestCase(f"P{i}", "", *inputs, "") for i, inputs in enumerate(mutation.probe_inputs(SPEC))]


def case(tc_id, speed, obstacle, age, expected="NO_ACTION"):
    return TestCase(tc_id, "REQ-01", speed, obstacle, age, expected)


def test_conditions_are_decided_from_the_inputs():
    facts = SPEC.facts(case("T", 30.0, None, 200))
    assert facts == {
        "C-SPEED-LOW": False, "C-SPEED-HIGH": False, "C-SENSOR-OLD": True,
        "C-SPEED-BRAKE": True, "C-OBSTACLE": False, "C-IN-RANGE": False,
    }
    assert SPEC.facts(case("T", 29.9, 20.0, 199))["C-SPEED-BRAKE"] is False
    assert SPEC.facts(case("T", 30.0, 20.0, 199))["C-IN-RANGE"] is True
    assert SPEC.facts(case("T", 30.0, 20.1, 199))["C-IN-RANGE"] is False


def test_every_input_belongs_to_exactly_one_class():
    for probe in PROBES:
        facts = SPEC.facts(probe)
        matching = [
            p["id"] for p in SPEC.partitions
            if all(facts[cid] == wanted for cid, wanted in p["when"].items())
        ]
        assert len(matching) == 1, (probe.inputs, matching)


def test_the_reference_gives_one_output_per_class():
    # The classes are a test design artifact and name no output. This checks that
    # they are fine enough: inputs of one class never need different outputs.
    outputs = {}
    for probe in PROBES:
        outputs.setdefault(SPEC.partition_of(probe), set()).add(decide(*probe.inputs).value)
    assert len(outputs) == len(SPEC.partitions)
    assert all(len(values) == 1 for values in outputs.values())


def test_spec_text_for_prompts_names_no_output():
    text = SPEC.condition_text() + " ".join(p["text"] for p in SPEC.partitions)
    assert not any(output in text for output in SPEC.outputs)


def test_partition_check_lists_classes_without_a_test():
    tests = [case("T1", 40.0, 10.0, 50), case("T2", 10.0, 10.0, 50)]
    missing = {p["id"] for p in partition_check(tests, SPEC)}
    assert missing == {"P-SPEED-LOW", "P-SPEED-HIGH", "P-SENSOR-OLD", "P-NO-OBSTACLE", "P-FAR"}
    assert partition_coverage(tests, SPEC) == 2 / 7
    assert partition_check(PROBES, SPEC) == []


def test_grounded_cross_check_shows_facts_and_no_values():
    tests = [case("T1", 47.3, 13.7, 123, "BRAKE")]
    llm = ScriptedClient(["tc_id,expected\nT1,BRAKE"] * 3)
    flagged, _ = cross_check(tests, llm, SPEC)
    cases = llm.calls[0][1].split("Cases:")[1]
    assert flagged == {}
    assert "speed is at least 30 km/h: yes" in cases
    assert "sensor data is 200 ms old or older: no" in cases
    assert not any(value in cases for value in ("47.3", "13.7", "123"))
    assert "BRAKE" not in cases


def test_ungrounded_cross_check_still_shows_the_values():
    tests = [case("T1", 47.3, 13.7, 123, "BRAKE")]
    llm = ScriptedClient(["tc_id,expected\nT1,BRAKE"] * 3)
    cross_check(tests, llm, SPEC, grounded=False)
    assert "47.3" in llm.calls[0][1]


def test_feedback_names_missing_classes_and_the_facts_of_a_disputed_test():
    classes = [p for p in SPEC.partitions if p["id"] == "P-NO-OBSTACLE"]
    text = render_feedback([], {"T1": "FAULT"}, [], classes, {"T1": "speed is below 0 km/h: yes"})
    assert "Input classes with no test" in text and "no obstacle detected" in text
    assert "T1 (speed is below 0 km/h: yes): an independent recomputation gives FAULT" in text


def test_refine_asks_for_missing_classes():
    start = [case("T1", 40.0, 10.0, 50, "BRAKE")]
    llm = ScriptedClient(["```csv\n" + to_csv(start) + "```"])
    _, _, calls, _ = refine(llm, SPEC, start, [], decide, enabled={"partition"}, max_rounds=1)
    assert "Input classes with no test" in calls[0]["prompt"]


def test_variants_differ_in_exactly_what_their_names_say():
    procedure, full = FR_VARIANTS["FR"]
    assert procedure is extend
    assert full - FR_VARIANTS["FR-coverage"][1] == {"boundary", "partition"}
    assert full - FR_VARIANTS["FR-cross"][1] == {"cross"}
    assert full - FR_VARIANTS["FR-mutation"][1] == {"mutation"}
    assert FR_VARIANTS["FR-self"][1] == (full - {"cross"}) | {"cross-self"}
    assert FR_VARIANTS["FR-rewrite"] == (refine, full)
    assert all(procedure is extend for name, (procedure, _) in FR_VARIANTS.items() if name != "FR-rewrite")


# The additive procedure


def addition(*rows):
    header = "tc_id,req_id,speed_kph,obstacle_m,sensor_age_ms,expected\n"
    return "```csv\n" + header + "\n".join(rows) + "\n```"


def test_extend_keeps_existing_tests_and_appends_new_ones():
    start = [case("T1", 40.0, 10.0, 50, "BRAKE")]
    llm = ScriptedClient([addition("X,REQ-02,10.0,10.0,50,NO_ACTION", "Y,REQ-01,40.0,10.0,50,FAULT")])
    result, errors, calls, rounds = extend(llm, SPEC, start, [], decide, enabled={"partition"}, max_rounds=1)
    assert result[0] == start[0]                         # untouched, same object content
    assert [t.tc_id for t in result] == ["T1", "R1-01"]  # the repeated input was not added again
    assert (errors, rounds, [c["kind"] for c in calls]) == (0, 1, ["extend"])


def test_extend_prompt_shows_inputs_but_not_the_existing_expected_results():
    start = [case("T1", 40.0, 10.0, 50, "BRAKE")]
    llm = ScriptedClient([addition("X,REQ-02,10.0,10.0,50,NO_ACTION")])
    extend(llm, SPEC, start, [], decide, enabled={"partition"}, max_rounds=1)
    listing = llm.calls[0][1].split("Inputs of the existing test cases:")[1].split("Findings:")[0]
    assert "T1,REQ-01,40,10,50" in listing and "BRAKE" not in listing


def test_extend_stops_when_nothing_usable_is_added():
    start = [case("T1", 40.0, 10.0, 50, "BRAKE")]
    llm = ScriptedClient(["I have nothing to add."] * 3)
    result, _, calls, rounds = extend(llm, SPEC, start, [], decide, enabled={"partition"})
    assert result == start and rounds == 1 and len(calls) == 1


def test_extend_applies_the_majority_of_the_final_vote_itself():
    # Both stated results are wrong. The model is never asked to correct them.
    start = [case("T1", 40.0, 10.0, 50, "NO_ACTION"), case("T2", 10.0, 10.0, 50, "BRAKE")]
    ballots = [
        "tc_id,expected\nT1,BRAKE\nT2,NO_ACTION",
        "tc_id,expected\nT1,BRAKE\nT2,FAULT",
        "tc_id,expected\nT1,FAULT\nT2,NO_ACTION",
    ]
    llm = ScriptedClient(ballots)
    result, _, calls, rounds = extend(llm, SPEC, start, [], decide, enabled={"cross"})
    assert [t.expected for t in result] == ["BRAKE", "NO_ACTION"]
    assert rounds == 0 and [c["kind"] for c in calls] == ["cross_check"] * 3
    assert [c["round"] for c in calls] == [1, 1, 1]


def test_a_result_without_a_majority_is_left_as_stated():
    start = [case("T1", 40.0, 10.0, 50, "NO_ACTION")]
    llm = ScriptedClient(["tc_id,expected\nT1,BRAKE", "tc_id,expected\nT1,FAULT", "tc_id,expected\nT1,NO_ACTION"])
    result, _, _, _ = extend(llm, SPEC, start, [], decide, enabled={"cross"})
    assert result[0].expected == "NO_ACTION"


def test_cross_check_votes_in_batches():
    tests = [case(f"T{i}", 40.0, 10.0, 50, "BRAKE") for i in range(45)]
    first = "tc_id,expected\n" + "\n".join(f"T{i},BRAKE" for i in range(40))
    second = "tc_id,expected\n" + "\n".join(f"T{i},FAULT" for i in range(40, 45))
    llm = ScriptedClient([first] * 3 + [second] * 3)
    flagged, calls = cross_check(tests, llm, SPEC)
    assert len(calls) == 6
    assert flagged == {f"T{i}": "FAULT" for i in range(40, 45)}

from sut.aeb import decide
from tcgen import mutation
from tcgen.spec import load_spec

SPEC = load_spec()
MUTANTS = mutation.generate()


def test_mutants_cover_every_operator_kind():
    assert {m.kind for m in MUTANTS} == {"relational", "logical", "constant", "return"}
    assert len({m.mutant_id for m in MUTANTS}) == len(MUTANTS)


def test_each_mutant_differs_from_the_source_in_text():
    source = mutation.SOURCE.read_text(encoding="utf-8")
    import ast

    reference = ast.unparse(ast.parse(source))
    assert all(m.source != reference for m in MUTANTS)


def test_split_is_a_partition_and_reproducible():
    feedback, evaluation = mutation.split(MUTANTS)
    ids = lambda group: {m.mutant_id for m in group}
    assert ids(feedback) & ids(evaluation) == set()
    assert ids(feedback) | ids(evaluation) == ids(MUTANTS)
    assert abs(len(feedback) - len(evaluation)) <= len({m.kind for m in MUTANTS})
    again_feedback, _ = mutation.split(MUTANTS)
    assert ids(again_feedback) == ids(feedback)


def test_split_balances_each_kind():
    feedback, evaluation = mutation.split(MUTANTS)
    for kind in {m.kind for m in MUTANTS}:
        in_feedback = sum(m.kind == kind for m in feedback)
        in_evaluation = sum(m.kind == kind for m in evaluation)
        assert abs(in_feedback - in_evaluation) <= 1


def test_a_boundary_mutant_is_distinguished_by_the_probes():
    probes = mutation.probe_inputs(SPEC)
    relational = next(m for m in MUTANTS if "speed_kph >= BRAKE_SPEED_KPH" in m.original and m.kind == "relational")
    probe = mutation.distinguishing_input(relational.load(), decide, probes)
    assert probe is not None
    assert probe[0] == 30.0


def test_equivalence_candidates_are_a_subset():
    candidates = mutation.equivalence_candidates(MUTANTS, decide, SPEC)
    assert set(c.mutant_id for c in candidates) <= set(m.mutant_id for m in MUTANTS)
